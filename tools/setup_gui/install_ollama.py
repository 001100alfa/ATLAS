"""Taşınabilir, anahtarsız Ollama kurucusu (yalnız stdlib).

Sihirbazın "İndir ve kur" düğmesi bunu bir iş olarak çalıştırır. Yaptığı:

  1. Resmi Ollama zip'ini indirir (yönetici hakkı GEREKMEZ, sisteme kurulmaz)
  2. `tools/ollama/` altına açar — proje klasörüyle birlikte taşınır
  3. Sunucuyu 127.0.0.1:11435'te başlatır (sistem kurulumunun 11434'üne dokunmaz)
  4. Seçilen modeli proje-yerel model deposuna indirir

Çıktı satır satır basılır; sihirbaz bunu canlı log olarak gösterir.

Elle de çalıştırılabilir:
    python -m tools.setup_gui.install_ollama --model llama3.2:3b
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from .detect import IS_WIN, OLLAMA_PORT, _exe, project_root

# Sabitlenmiş sürüm (bilinçli yükseltin): indirme URL'si ve arşiv düzeni bu
# sürümle doğrulandı — ~1.36 GB, ollama.exe arşiv kökünde, runner'lar lib/ altında.
OLLAMA_VERSION = "v0.32.3"
ASSET = "ollama-windows-amd64.zip"
RELEASE_URL = "https://github.com/ollama/ollama/releases/download/{ver}/{asset}"

# Model adı doğrulaması: kabuk kullanılmıyor ama yine de dar tutuyoruz.
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,60}(:[A-Za-z0-9._-]{1,30})?$")


def log(msg: str) -> None:
    """Sihirbazın canlı log'una tek satır (tamponlanmadan)."""
    print(msg, flush=True)


def _human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def _expected_total(resp, have: int) -> int | None:
    """Yanıttan dosyanın TAM boyutunu çıkarır (kısmi yanıtta Content-Range'den)."""
    rng = resp.headers.get("Content-Range")  # "bytes 100-999/1000"
    if rng and "/" in rng:
        tail = rng.rsplit("/", 1)[-1].strip()
        if tail.isdigit():
            return int(tail)
    clen = int(resp.headers.get("Content-Length") or 0)
    return (have + clen) if clen else None


def download(url: str, dest: Path, label: str = "indiriliyor", attempts: int = 6) -> None:
    """Doğrulanmış, kaldığı yerden devam edebilen indirme.

    ÖLÇÜLDÜ: yavaş bağlantıda akış tamamlanmadan kapanabiliyor (1,4 GB'lık
    arşivde %82'de kesildi). Eski sürüm bunu "bitti" sayıp yarım dosyayı teslim
    ediyordu; sonuç "arşiv bozuk" hatasıydı. Bu yüzden:
      * indirilen boyut beklenenle KARŞILAŞTIRILIR,
      * eksikse `.part` SİLİNMEZ; `Range` ile kalınan yerden devam edilir,
      * geçici ağ hataları birkaç kez yeniden denenir.
    """
    tmp = dest.with_suffix(dest.suffix + ".part")
    log(f"[1/4] {label}: {url}")
    started = last = time.monotonic()
    total: int | None = None

    for attempt in range(1, attempts + 1):
        have = tmp.stat().st_size if tmp.is_file() else 0
        if have:
            log(f"      kaldığı yerden devam: {_human(have)}")
        req = urllib.request.Request(url)
        if have:
            req.add_header("Range", f"bytes={have}-")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                # 206 = kısmi içerik (devam kabul edildi); 200 = sunucu Range'i
                # yok saydı, baştan yazmalıyız.
                resuming = have > 0 and getattr(resp, "status", 200) == 206
                if have and not resuming:
                    log("      sunucu devam etmeyi kabul etmedi, baştan indiriliyor")
                    have = 0
                total = _expected_total(resp, have) or total
                if attempt == 1 and total:
                    log(f"      toplam {_human(total)} - bağlantı hızına göre uzun sürebilir")
                got = have
                with tmp.open("ab" if resuming else "wb") as fh:
                    while chunk := resp.read(1024 * 256):
                        fh.write(chunk)
                        got += len(chunk)
                        now = time.monotonic()
                        # Saniyede bir satır: log'u boğmadan ilerlemeyi göster.
                        # Yüzde ondalıklı - büyük dosyada tam sayı uzun süre "%0"
                        # kalıp kullanıcıya donmuş izlenimi veriyordu (ölçüldü).
                        if now - last >= 2.0:
                            last = now
                            speed = (got - have) / max(now - started, 0.001)
                            if total:
                                pct = got * 100 / total
                                eta = (total - got) / speed if speed > 0 else 0
                                log(
                                    f"      %{pct:.1f} ({_human(got)} / {_human(total)}) "
                                    f"· {_human(speed)}/sn · kalan ~{eta / 60:.0f} dk"
                                )
                            else:
                                log(f"      {_human(got)} · {_human(speed)}/sn")
        except (urllib.error.URLError, OSError) as exc:
            log(f"      [uyarı] bağlantı hatası ({attempt}/{attempts}): {exc}")
            time.sleep(min(5 * attempt, 20))
            continue

        got = tmp.stat().st_size if tmp.is_file() else 0
        if total and got < total:
            # Akış erken kapandı: .part DURSUN, sonraki tur devam etsin.
            log(f"      [uyarı] eksik indi ({_human(got)} / {_human(total)}) - devam edilecek")
            started = time.monotonic()
            time.sleep(2)
            continue
        break
    else:
        raise RuntimeError(f"indirme {attempts} denemede tamamlanamadı (yarım dosya: {tmp})")

    got = tmp.stat().st_size if tmp.is_file() else 0
    if total and got != total:
        raise RuntimeError(f"boyut uyuşmuyor: {got} != {total} (yarım dosya: {tmp})")
    tmp.replace(dest)
    log(f"      tamam ({_human(dest.stat().st_size)})")


def install_binary(root: Path, force: bool = False) -> Path:
    """Ollama ikilisini ve runner'larını tools/ollama/ altına kurar."""
    target = root / "tools" / "ollama"
    exe = target / _exe("ollama")
    if exe.is_file() and not force:
        log(f"[1/4] Ollama zaten kurulu: {exe}")
        return exe
    if not IS_WIN:
        raise RuntimeError("Otomatik kurulum şimdilik yalnız Windows için; ollama.com/download")

    target.mkdir(parents=True, exist_ok=True)
    zip_path = target / ASSET
    download(RELEASE_URL.format(ver=OLLAMA_VERSION, asset=ASSET), zip_path, "Ollama indiriliyor")

    log(f"[2/4] Açılıyor → {target}")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target)
    except zipfile.BadZipFile as exc:
        zip_path.unlink(missing_ok=True)
        raise RuntimeError(f"arşiv bozuk: {exc}") from exc
    zip_path.unlink(missing_ok=True)

    if not exe.is_file():
        raise RuntimeError(f"ollama.exe beklenen yerde yok: {exe} (arşiv düzeni değişmiş olabilir)")
    log("      tamam")
    return exe


def _env(root: Path) -> dict[str, str]:
    """Model deposu proje içinde, sunucu yalnız yerel portta."""
    return {
        **os.environ,
        "OLLAMA_MODELS": str(root / "tools" / "ollama" / "models"),
        "OLLAMA_HOST": f"127.0.0.1:{OLLAMA_PORT}",
    }


def server_ready(exe: Path, root: Path, timeout: float = 30.0) -> bool:
    """`ollama list` çalışıyorsa sunucu ayakta demektir."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = subprocess.run(
                [str(exe), "list"],
                env=_env(root),
                capture_output=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if r.returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            pass
        time.sleep(1)
    return False


def start_server(root: Path, exe: Path | None = None) -> bool:
    """Sunucuyu ayrı süreçte başlatır (zaten çalışıyorsa dokunmaz)."""
    exe = exe or root / "tools" / "ollama" / _exe("ollama")
    if not exe.is_file():
        log("[HATA] Ollama kurulu değil.")
        return False
    if server_ready(exe, root, timeout=3):
        log(f"[3/4] Sunucu zaten çalışıyor (127.0.0.1:{OLLAMA_PORT}).")
        return True

    log(f"[3/4] Sunucu başlatılıyor: 127.0.0.1:{OLLAMA_PORT}")
    # DETACHED: sihirbaz kapansa da model sunucusu ayakta kalsın.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
        subprocess, "DETACHED_PROCESS", 0
    )
    subprocess.Popen(
        [str(exe), "serve"],
        env=_env(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=flags,
        close_fds=True,
    )
    if not server_ready(exe, root, timeout=40):
        log("[HATA] Sunucu açılmadı (port engelli olabilir).")
        return False
    log("      hazır")
    return True


def pull_model(root: Path, model: str, exe: Path | None = None) -> bool:
    """Modeli proje-yerel depoya indirir; ilerlemeyi sadeleştirerek basar."""
    if not MODEL_RE.match(model):
        log(f"[HATA] geçersiz model adı: {model!r}")
        return False
    exe = exe or root / "tools" / "ollama" / _exe("ollama")
    log(f"[4/4] Model indiriliyor: {model} (büyük dosya, sabırlı olun)")

    proc = subprocess.Popen(
        [str(exe), "pull", model],
        env=_env(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert proc.stdout is not None
    last, buf = 0.0, ""
    while True:
        ch = proc.stdout.read(1)
        if not ch:
            break
        # ollama ilerlemeyi \r ile yeniler; son parçayı saniyede bir basıyoruz.
        if ch in "\r\n":
            now = time.monotonic()
            line = buf.strip()
            buf = ""
            if line and (now - last >= 1.0 or "success" in line.lower()):
                last = now
                log(f"      {line[:110]}")
        else:
            buf += ch
    code = proc.wait()
    if code != 0:
        log(f"[HATA] model indirilemedi (çıkış {code}).")
        return False
    log("      model hazır")
    return True


def install(root: Path | None = None, model: str = "llama3.2:3b", force: bool = False) -> int:
    """Tam akış: ikili → sunucu → model. Çıkış kodu döndürür."""
    root = root or project_root()
    free = shutil.disk_usage(root).free
    log(f"Boş disk alanı: {_human(free)}")
    if free < 6 * 1024**3:
        log("[UYARI] 6 GB'tan az boş alan var; indirme yarıda kalabilir.")
    try:
        exe = install_binary(root, force=force)
    except RuntimeError as exc:
        log(f"[HATA] {exc}")
        return 1
    if not start_server(root, exe):
        return 1
    if not pull_model(root, model, exe):
        return 1
    log("")
    log(f"Bitti. Yerel model sunucusu 127.0.0.1:{OLLAMA_PORT} adresinde çalışıyor.")
    log("Artık Goose ajanını hesap açmadan bağlayabilirsiniz.")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Taşınabilir Ollama kurulumu")
    ap.add_argument("--model", default="llama3.2:3b", help="indirilecek model etiketi")
    ap.add_argument("--force", action="store_true", help="ikiliyi yeniden indir")
    ns = ap.parse_args()
    return install(model=ns.model, force=ns.force)


if __name__ == "__main__":
    raise SystemExit(main())

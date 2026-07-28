"""Klasörü sıkıştırmadan önce hazırlar (PAKETLE.cmd).

Amaç: arşiv TUTARLI olsun ve karşı tarafta ilk açılışta kendini uyarlasın.

Yapılanlar:

1. **Süreçleri durdur** — çalışan ajan/panel/model süreçleri dosyaları kilitler;
   ÖLÇÜLDÜ (2026-07-27): kilitli `cline.exe` yüzünden `npm install` EBUSY,
   `goose.exe` yüzünden klasör taşıma "Permission denied" verdi. Kilitli dosya
   arşive yarım girer.
2. **Makine parmak izini sil** — karşı tarafta ilk `BASLAT.cmd` "yeni yerleşim"
   görüp sarmalayıcıları/kayıtları yeniden üretir.
3. **Rapor** — neyin taşındığı, boyutu ve eksikse ne eksik.

Hiçbir kullanıcı verisi silinmez. Büyük ama gereksiz olanları atmak isterseniz
`--yagsiz` verin: yalnız yeniden üretilebilir önbellekler (indirme arşivleri,
__pycache__, test/lint önbellekleri) temizlenir.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from tools.doctor_gui import processes

from . import relocate

# Yeniden üretilebilir, taşımaya değmez (yalnız --yagsiz ile silinir).
# Yollar AÇIK yazılır: `rglob("__pycache__")` bütün ağacı (node_modules dahil,
# ~5 GB) tarar ve paketlemeyi dakikalarca uzatır.
SLIM_TARGETS = (
    ("tools/.cache", "indirilen kurulum arsivleri"),
    (".pytest_cache", "test onbellegi"),
    (".ruff_cache", "lint onbellegi"),
    (".mypy_cache", "tip onbellegi"),
)
# __pycache__ yalnız kendi kaynak ağacımızda süpürülür.
PYCACHE_ROOTS = ("src", "tools", "tests")

# Arşivleyiciler — bulunanla paketlenir (`--arsiv`).
ARCHIVERS = (
    (r"C:\Program Files\WinRAR\Rar.exe", ["a", "-r", "-ep1", "-m1"]),
    (r"C:\Program Files\7-Zip\7z.exe", ["a", "-mx1"]),
)


def dir_size(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            pass  # erisilemeyen dosya boyut raporunu durdurmaz
    return total


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} GB"


def stop_everything(root: Path) -> dict:
    """Depo İÇİNDEKİ ajan süreçlerini kapatır (başka kurulumlara dokunmaz).

    Panel açıkken `stray()` bilinçli olarak boş döner (o süreçler kullanımda
    olabilir) — bu yüzden paketlemeden önce paneli kapatmak gerekir; rapor bunu
    söyler.
    """
    if processes.juggler_running(root):
        return {"found": 0, "killed": 0, "panel_open": True}
    found = processes.stray(root)
    res = processes.kill([p["pid"] for p in found]) if found else {"killed": [], "failed": []}
    return {
        "found": len(found),
        "killed": len(res.get("killed") or []),
        "panel_open": False,
        "detail": res,
    }


def slim(root: Path) -> list[dict]:
    out = []
    targets = [(root / rel, why) for rel, why in SLIM_TARGETS]
    for sub in PYCACHE_ROOTS:
        d = root / sub
        if d.is_dir():
            targets += [(p, "python bytecode") for p in d.rglob("__pycache__")]
    for path, why in targets:
        if path.is_dir():
            size = dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            out.append({"path": str(path.relative_to(root)), "freed": size, "why": why})
    return out


def find_archiver() -> tuple[Path, list[str]] | None:
    for exe, args in ARCHIVERS:
        p = Path(exe)
        if p.is_file():
            return p, args
    return None


def make_archive(root: Path, dst: Path) -> dict:
    """RAR/7z ile arşivler (kurulu değilse elle sıkıştırma yönergesi döner)."""
    tool = find_archiver()
    if not tool:
        return {
            "ok": False,
            "detail": "WinRAR/7-Zip bulunamadi - klasore sag tiklayip kendiniz sikistirin.",
        }
    exe, args = tool
    argv = [str(exe), *args, str(dst), "."]
    res = subprocess.run(argv, cwd=str(root), capture_output=True, text=True)  # noqa: S603
    ok = res.returncode == 0 and dst.exists()
    return {
        "ok": ok,
        "detail": f"{dst} ({human(dst.stat().st_size)})" if ok else (res.stderr or "")[-300:],
        "tool": exe.name,
    }


def prepare(root: Path, do_slim: bool = False) -> dict:
    report: dict = {}
    report["processes"] = stop_everything(root)
    report["slim"] = slim(root) if do_slim else []
    fp = relocate.state_path(root)
    if fp.is_file():
        fp.unlink()
        report["fingerprint"] = "silindi (karsi tarafta yeniden uretilir)"
    else:
        report["fingerprint"] = "zaten yok"
    report["preflight"] = relocate.preflight(root)
    report["size"] = dir_size(root)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Tasima icin hazirla")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--yagsiz", action="store_true", help="yeniden uretilebilir onbellekleri sil")
    ap.add_argument("--arsiv", type=Path, default=None, help="hedef .rar/.7z yolu (varsa uretir)")
    args = ap.parse_args(argv)
    root = args.root.resolve()

    print(f"ATLAS paketleme - {root}\n")
    rep = prepare(root, args.yagsiz)

    p = rep["processes"]
    if p.get("panel_open"):
        print("! Panel ACIK - once kapatin, sonra bu betigi tekrar calistirin.")
        print("  (Panel acikken surec temizligi bilincli olarak yapilmaz.)")
    else:
        print(f"Calisan ajan sureci: {p['found']} bulundu, {p['killed']} kapatildi")
    for item in rep["slim"]:
        print(f"  temizlendi: {item['path']} ({human(item['freed'])}) - {item['why']}")
    print(f"Makine parmak izi: {rep['fingerprint']}")

    print("\nTasinan bilesenler:")
    for c in rep["preflight"]:
        mark = "+" if c["ok"] else "-"
        extra = "" if c["portable"] else "  (MAKINEYE BAGLI - karsi tarafta olmayabilir)"
        print(f"  {mark} {c['id']}: {c['detail']}{extra}")

    print(f"\nToplam boyut: {human(rep['size'])}")

    if args.arsiv:
        print("\nArsivleniyor (birkac dakika surebilir)...")
        res = make_archive(root, args.arsiv.resolve())
        print(("OK   " if res["ok"] else "HATA ") + res["detail"])
        return 0 if res["ok"] else 1

    print("\nSimdi klasoru sikistirin (WinRAR: sag tik > Add to archive).")
    print("Karsi makinede: arsivi acin ve BASLAT.cmd'ye cift tiklayin. Hepsi bu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

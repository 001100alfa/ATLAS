"""Düzeltme eylemleri — bulguların "Düzelt" düğmesinin arkasındaki iş.

İki tür eylem vardır:

* **anlık** (`instant`) — saniyeler içinde biter, sonucu doğrudan döner
  (dosya kopyalama, kayıt yazma, sunucu başlatma).
* **iş** (`job`) — uzun sürer, çıktısı canlı akar (npm/pip kurulumu, çekirdek
  kurulum betikleri).

Her eylem **idempotent**tir: iki kez çalıştırmak zarar vermez. Hiçbir eylem
kullanıcı verisini silmez; geri dönüşü olan tek yıkıcı işlem `juggler-restore`
ve o da yalnız daha önce ALINMIŞ yedeği geri yazar.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from tools.juggler_profile import sync as profile_sync
from tools.portable import runtimes
from tools.setup_gui import connect as connect_mod
from tools.setup_gui import wrappers
from tools.setup_gui.detect import IS_WIN, _exe
from tools.setup_gui.install_ollama import start_server

from . import processes, versions
from .checks import (
    backup_dir,
    backup_tag,
    backups_root,
    ext_installed_dir,
    ext_source_dir,
    list_backups,
    sha256_file,
    write_baseline,
)

# --- anlık eylemler -----------------------------------------------------------


def _ext_install(root: Path) -> dict:
    src, dst = ext_source_dir(root), ext_installed_dir(root)
    if not src.is_dir():
        return {"ok": False, "detail": f"kaynak yok: {src}"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return {
        "ok": True,
        "detail": f"Eklenti kopyalandı → {dst}",
        "note": "Panel açıksa kapatıp yeniden açın (eklentiler açılışta okunur).",
    }


def _register(root: Path) -> dict:
    res = connect_mod.register_agents(root)
    wrappers.generate(root)
    written = ", ".join(res["written"]) or "—"
    return {
        "ok": bool(res["written"]),
        "detail": f"Kayıt yenilendi ({written}) → {res['path']}",
        "note": "Yollar mevcut kuruluma göre yeniden yazıldı; panelde ajanı tekrar deneyin.",
    }


def _ollama_start(root: Path) -> dict:
    ok = start_server(root)
    return {
        "ok": ok,
        "detail": "Yerel model sunucusu çalışıyor." if ok else "Sunucu başlatılamadı.",
        "note": "" if ok else "Taşınabilir Ollama kurulu mu? SETUP.cmd → 'Yerel AI'.",
    }


def _juggler_backup(root: Path) -> dict:
    """Çalışan panel ikililerini SÜRÜM ETİKETLİ kendi klasörüne kopyalar.

    Hedef sabit değildir (`juggler-backup-v0.5.0-73e41a6`): tek bir klasör her
    yedek almada bir öncekini eziyordu, yani ikinci yedek elindeki tek geri
    dönüş noktasını siliyordu. Aynı yapıyı yeniden yedeklemek aynı klasörü
    tazeler; farklı yapı yeni klasör açar.
    """
    ver = versions.local_versions(root)["juggler"] or ""
    src_dir = root / "tools" / "juggler"
    d = backup_dir(root, backup_tag(ver, src_dir / _exe("juggler")))
    d.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in (_exe("juggler"), _exe("juggler-app")):
        src = src_dir / name
        if src.is_file():
            shutil.copy2(src, d / name)
            copied.append(name)
    if not copied:
        return {"ok": False, "detail": "Yedeklenecek ikili yok (tools/juggler boş)."}
    # Sürümün YANINDA parmak izleri: "hangi dosya değişti?" tahminle değil
    # karşılaştırmayla yanıtlanır (panel kendini sessizce güncelleyebiliyor).
    lines = [ver or "bilinmiyor", ""]
    lines += [f"{name}  sha256={sha256_file(d / name)}" for name in copied]
    (d / "VERSION.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    others = [b for b in list_backups(root) if b["name"] != d.name]
    return {
        "ok": True,
        "detail": f"Yedek alındı ({', '.join(copied)}) → {d.name}",
        "note": f"Kaydedilen sürüm: {ver or 'bilinmiyor'}. "
        + (f"Korunan diğer yedekler: {len(others)}. " if others else "")
        + "Güncelleme bozarsa 'Yedekten geri al' yeterli.",
    }


def _juggler_restore(root: Path, name: str = "") -> dict:
    """Yedeği geri yazar. `name` verilmezse EN YENİ yedek kullanılır."""
    backups = list_backups(root)
    if not backups:
        return {"ok": False, "detail": f"Yedek bulunamadı: {backups_root(root)}"}
    chosen = next((b for b in backups if b["name"] == name), None) if name else backups[0]
    if chosen is None:
        return {"ok": False, "detail": f"Yedek bulunamadı: {name}"}

    d = Path(chosen["path"])
    dst = root / "tools" / "juggler"
    restored = []
    for exe_name in (_exe("juggler"), _exe("juggler-app")):
        src = d / exe_name
        if src.is_file():
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst / exe_name)
            restored.append(exe_name)
    if not restored:
        return {"ok": False, "detail": f"Yedek bulunamadı: {d}"}
    return {
        "ok": True,
        "detail": f"Yedek geri yüklendi ({', '.join(restored)}) — sürüm {chosen['version']}",
        "note": f"Kaynak: {chosen['name']}"
        + (f" · {len(backups) - 1} yedek daha var." if len(backups) > 1 else "")
        + " Panel açıksa kapatıp yeniden açın.",
    }


def _save_baseline(root: Path) -> dict:
    now = versions.local_versions(root)
    p = write_baseline(root, now)
    return {
        "ok": True,
        "detail": f"Sağlıklı sürümler kaydedildi → {p}",
        "note": "Bundan sonra herhangi bir bileşen güncellenirse 'Sürüm izi' adımı gösterir.",
    }


def _juggler_update_guide(root: Path) -> dict:
    """Panel güncellemesi otomatik yapılmaz — nedeni ve güvenli yolu anlatır."""
    latest = versions.remote_latest("juggler")
    have_backup = bool(list_backups(root))
    return {
        "ok": True,
        "detail": f"Üstakım sürümü: {('v' + latest) if latest else 'sorgulanamadı'}",
        "note": (
            "Panel ikilisi ATLAS tarafından İNDİRİLMEZ: AGPL lisanslı ayrı bir uygulamadır "
            "ve kaynaktan derlenir. Güvenli sıra: (1) "
            + ("yedek zaten var" if have_backup else "önce 'Şimdi yedek al'")
            + ", (2) yeni sürümü AYRI bir klasöre klonlayıp derleyin, (3) bu ekrandaki "
            "'Eklenti ↔ panel uyumluluğu' denetimini yeni ikiliyle tekrarlayın, (4) ancak "
            "geçerse tools/juggler/ içine kopyalayın. Ayrıntı: docs/JUGGLER.md."
        ),
    }


def _auth_hint(root: Path, agent: str = "") -> dict:
    info = connect_mod.auth_command(agent, root) if agent else {"ok": False}
    if not info.get("ok"):
        return {
            "ok": True,
            "detail": "Giriş, SETUP.cmd → 'Ajanları bağla' ekranından yapılır.",
            "note": "Sihirbaz doğru komutu sizin adınıza açar; parola/kod her zaman sizde kalır.",
        }
    return {
        "ok": True,
        "detail": info["command"],
        "note": "Bu komutu SETUP.cmd → 'Ajanları bağla' ekranındaki 'Giriş yap' düğmesi "
        "sizin için çalıştırır.",
    }


def _profile_sync(root: Path) -> dict:
    """Profili kurar/tazeler — kayıtları ATLAS'ın kendi sarmalayıcılarına çevirir."""
    r = profile_sync.sync(root)
    return {
        "ok": bool(r.get("ok")),
        "detail": "\n".join(r.get("log") or []),
        "note": "Panel açıksa kapatıp yeniden açın; başlatıcılar JUGGLER_CONFIG_DIR'i "
        "profile çevirir, böylece Juggler klasörü silinse de ATLAS tarafı ayakta kalır.",
    }


def _kill_stray(root: Path) -> dict:
    """Depoya ait öksüz ajan süreçlerini kapatır (panel açıkken hiçbir şey yapmaz)."""
    found = processes.stray(root)
    if not found:
        return {"ok": True, "detail": "Kapatılacak artık süreç yok."}
    res = processes.kill([p["pid"] for p in found])
    ok = not res["failed"]
    gone = len(res.get("gone") or [])
    return {
        "ok": ok,
        "detail": f"{len(res['killed'])} süreç kapatıldı"
        + (f", {gone} tanesi zaten sonlanmıştı (alt süreçler)" if gone else "")
        + (f", {len(res['failed'])} kapatılamadı" if res["failed"] else ""),
        "note": "Panel açıldığında ajanlar yeniden başlatılır; hiçbir oturum kaybolmaz."
        if ok
        else "Kapatılamayanlar: " + "; ".join(str(x) for x in res["failed"][:3]),
    }


INSTANT = {
    "kill-stray": _kill_stray,
    "profile-sync": _profile_sync,
    "ext-install": _ext_install,
    "register": _register,
    "ollama-start": _ollama_start,
    "juggler-backup": _juggler_backup,
    "juggler-restore": _juggler_restore,
    "save-baseline": _save_baseline,
    "update-juggler": _juggler_update_guide,
    "auth-hint": _auth_hint,
}


# --- uzun işler ---------------------------------------------------------------

# Güncellenebilir npm paketleri: ajan adı → paket adı.
NPM_PACKAGES = {"opencode": "opencode-ai", "kilo": "@kilocode/cli", "cline": "cline"}


def job_argv(action: str, root: Path) -> tuple[list[str], str] | None:
    """Uzun iş eylemini (argv, başlık) olarak verir; bilinmiyorsa None."""
    if action == "install-core":
        script = root / "setup-portable.cmd"
        return ((["cmd.exe", "/c", str(script)] if IS_WIN else [str(script)]), "Çekirdek kurulumu")
    if action in ("install-clis", "update-goose"):
        script = root / "setup-ai-cli.cmd"
        return ((["cmd.exe", "/c", str(script)] if IS_WIN else [str(script)]), "AI CLI kurulumu")

    if action.startswith("update-"):
        agent = action[len("update-") :]
        if agent in NPM_PACKAGES:
            # Depo icindeki node paketi npm'i de getirir; once o denenir ki
            # tasinan klasor npm kurulu OLMAYAN bir makinede de guncellenebilsin.
            npm = runtimes.npm_cmd(root)
            if not npm:
                return None
            prefix = root / "tools" / "ai-cli"
            argv = [npm, "install", f"{NPM_PACKAGES[agent]}@latest", "--prefix", str(prefix)]
            # npm Windows'ta .cmd shim'dir; cmd.exe üzerinden çağrılır.
            return ((["cmd.exe", "/c", *argv] if IS_WIN else argv), f"{agent} güncelleniyor")
        if agent == "kimi":
            py = (
                root
                / "tools"
                / "ai-cli"
                / "py-venv"
                / ("Scripts" if IS_WIN else "bin")
                / _exe("python")
            )
            exe = str(py) if py.is_file() else sys.executable
            return ([exe, "-m", "pip", "install", "-U", "kimi-cli"], "kimi güncelleniyor")
    return None


def is_known(action: str, root: Path) -> bool:
    return action in INSTANT or job_argv(action, root) is not None


def run_instant(action: str, root: Path, params: dict | None = None) -> dict:
    fn = INSTANT.get(action)
    if not fn:
        return {"ok": False, "detail": f"bilinmeyen eylem: {action}"}
    params = params or {}
    if action == "auth-hint":
        return fn(root, str(params.get("agent") or ""))
    if action == "juggler-restore":
        # Boş ad = en yeni yedek; arayüz belirli bir yedeği seçebilsin diye açık.
        return fn(root, str(params.get("name") or ""))
    return fn(root)

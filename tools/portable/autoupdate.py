"""Kendiliğinden güncelleme — kullanıcı sürüm takip etmesin diye.

Politika (`atlas-portable.json` ile değiştirilebilir):

* `agents`  (varsayılan) — npm/pip ajanları (opencode, kilo, cline, kimi)
  günde bir kez sessizce güncellenir.
* `notify`  — hiçbir şey kurulmaz, yalnız "şu güncellemeler var" denir.
* `off`     — denetim de yapılmaz.

**Panel ikilisi (juggler) HİÇBİR politikada otomatik güncellenmez.** Gerekçe
ölçülmüş bir olaydır (2026-07-27): panelin kendi güncelleyicisi çalışan
ikiliyi değiştirdi ve içindeki yerel yamalar (ACP `authenticate`) yok oldu,
ajanlar bağlanamaz hâle geldi. Panel için yalnız bildirim üretilir; kurulum
`DOCTOR.cmd`teki güvenli sırayla (yedek → ayrı klasörde derle → `ext validate`
→ kopyala) elle yapılır.

İnternet yoksa hiçbir şey kırılmaz: uzak sorgular `None` döner, sonuç
"denetlenemedi" olur ve açılış gecikmez.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from tools.doctor_gui import fixes, versions

CONFIG_NAME = "atlas-portable.json"
STATE_REL = (".atlas", "portable", "update.json")

# Otomatik güncellenebilecek ajanlar (hepsi paket yöneticisiyle kurulur ve
# kurulumu geri alınabilir). goose/ollama ikili indirmesidir, juggler ise
# kesinlikle elle — bu yüzden listede yoklar.
AUTO_AGENTS = ("opencode", "kilo", "cline", "kimi")
DEFAULTS = {"autoUpdate": "agents", "checkEveryHours": 24}


def config_path(root: Path) -> Path:
    return root / CONFIG_NAME


def load_config(root: Path) -> dict:
    p = config_path(root)
    cfg = dict(DEFAULTS)
    if p.is_file():
        try:
            user = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(user, dict):
                cfg.update({k: v for k, v in user.items() if k in DEFAULTS})
        except (OSError, json.JSONDecodeError):
            pass  # bozuk config açılışı engellemez; varsayılanla devam
    return cfg


def state_path(root: Path) -> Path:
    return root.joinpath(*STATE_REL)


def read_state(root: Path) -> dict:
    p = state_path(root)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(root: Path, data: dict) -> Path:
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def due(root: Path, now: float | None = None) -> bool:
    """Denetim zamanı geldi mi? (Her açılışta ağa çıkmak açılışı yavaşlatır.)"""
    cfg = load_config(root)
    if cfg["autoUpdate"] == "off":
        return False
    last = float(read_state(root).get("lastCheck") or 0)
    every = float(cfg["checkEveryHours"]) * 3600
    return (now if now is not None else time.time()) - last >= every


def find_updates(root: Path) -> list[dict]:
    """Güncellenebilir bileşenler. Ağ yoksa boş liste (hata değil)."""
    local = versions.local_versions(root)
    out: list[dict] = []
    for name in (*AUTO_AGENTS, "goose", "juggler"):
        latest = versions.remote_latest(name)
        if versions.is_outdated(local.get(name), latest):
            out.append(
                {
                    "name": name,
                    "local": local.get(name),
                    "latest": latest,
                    # Panel elle güncellenir — gerekçe modül başlığında.
                    "auto": name in AUTO_AGENTS,
                }
            )
    return out


def apply_update(root: Path, name: str, timeout: float = 900.0) -> dict:
    """Tek bileşeni günceller (yalnız otomatik listesindekiler)."""
    if name not in AUTO_AGENTS:
        return {"name": name, "ok": False, "detail": "otomatik güncellenmez (elle)"}
    job = fixes.job_argv(f"update-{name}", root)
    if not job:
        return {"name": name, "ok": False, "detail": "güncelleme komutu kurulamadı (npm yok?)"}
    argv, _title = job
    try:
        res = subprocess.run(  # noqa: S603 - argv sabit kaynaklardan üretilir
            argv, cwd=str(root), capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"name": name, "ok": False, "detail": str(exc)}
    ok = res.returncode == 0
    tail = (res.stderr or res.stdout or "").strip().splitlines()
    return {
        "name": name,
        "ok": ok,
        "detail": "güncellendi" if ok else (tail[-1] if tail else f"çıkış {res.returncode}"),
    }


def run(root: Path, force: bool = False) -> dict:
    """Açılışta çağrılan tek giriş: gerekirse denetle, politikaya göre uygula."""
    cfg = load_config(root)
    if cfg["autoUpdate"] == "off" and not force:
        return {"ok": True, "mode": "off", "checked": False, "updates": [], "applied": []}
    if not force and not due(root):
        st = read_state(root)
        return {
            "ok": True,
            "mode": cfg["autoUpdate"],
            "checked": False,
            "updates": st.get("updates") or [],
            "applied": [],
            "detail": "Denetim zamanı gelmedi.",
        }

    updates = find_updates(root)
    applied: list[dict] = []
    if cfg["autoUpdate"] == "agents":
        applied = [apply_update(root, u["name"]) for u in updates if u["auto"]]

    # Uygulananlar listeden düşsün ki bildirim yalnız KALAN işi göstersin.
    done = {a["name"] for a in applied if a["ok"]}
    remaining = [u for u in updates if u["name"] not in done]
    write_state(
        root,
        {
            "lastCheck": time.time(),
            "mode": cfg["autoUpdate"],
            "updates": remaining,
            "applied": applied,
        },
    )
    return {
        "ok": True,
        "mode": cfg["autoUpdate"],
        "checked": True,
        "updates": remaining,
        "applied": applied,
    }


def summary_lines(res: dict) -> list[str]:
    """Konsola basılacak kısa özet (kullanıcı sürüm tablosu okumasın)."""
    out: list[str] = []
    for a in res.get("applied") or []:
        out.append(("  guncellendi: " if a["ok"] else "  guncellenemedi: ") + a["name"])
    for u in res.get("updates") or []:
        if u["name"] == "juggler":
            out.append(
                f"  panel guncellemesi var (v{u['latest']}) - otomatik KURULMAZ, "
                "DOCTOR.cmd > guvenli sira"
            )
        elif not u["auto"]:
            out.append(f"  {u['name']}: yeni surum v{u['latest']} (elle: SETUP.cmd)")
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="ATLAS otomatik guncelleme")
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--force", action="store_true", help="zaman asimini bekleme")
    args = ap.parse_args()
    res = run(args.root, args.force)
    for line in summary_lines(res) or ["  guncelleme yok"]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

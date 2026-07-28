"""BASLAT.cmd'nin beyni: uyarla → güncelle → paneli aç.

Kullanıcının göreceği tek akış budur. Sırası kasıtlı:

1. **Uyarla** — klasör yeni bir makinede/yolda ise makineye özgü ne varsa
   yeniden üretilir (sarmalayıcılar, ACP kayıtları, profil). Değişmemişse
   milisaniyeler sürer.
2. **Denetle** — eksik çalışma zamanı/ikili varsa tek satırla söylenir; hiçbiri
   açılışı ENGELLEMEZ (bir ajan eksikse diğerleri çalışmaya devam eder).
3. **Güncelle** — politikaya göre (bkz. autoupdate) günde bir kez.
4. **Aç** — panel, ATLAS profiliyle başlatılır.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from tools.juggler_profile import sync as profile_sync

from . import autoupdate, relocate

PORT = 3939


def _say(line: str = "") -> None:
    print(line, flush=True)


def prepare(root: Path, force_relocate: bool = False) -> dict:
    """Panel açılmadan önceki her şey. Panel açılmasa da tek başına anlamlı."""
    needed, changed = relocate.needs_relocate(root)
    res = {"relocated": None, "preflight": [], "update": None}

    if needed or force_relocate:
        _say("Yeni yerlesim algilandi (" + ", ".join(changed) + ") - uyarlaniyor...")
        res["relocated"] = relocate.relocate(root, force=force_relocate)
        for step in res["relocated"]["steps"]:
            _say(("  " if step["ok"] else "  ! ") + f"{step['step']}: {step['detail']}")
    else:
        _say("Yerlesim guncel.")

    res["preflight"] = relocate.preflight(root)
    missing = [c for c in res["preflight"] if not c["ok"]]
    if missing:
        _say("Eksikler (calismaya engel degil):")
        for c in missing:
            _say(f"  - {c['id']}: {c['detail']} ({c['needed_by']} icin gerekli)")

    res["update"] = autoupdate.run(root)
    lines = autoupdate.summary_lines(res["update"])
    if lines:
        _say("Guncelleme:")
        for line in lines:
            _say(line)
    return res


def launch_panel(root: Path, port: int = PORT, wait: bool = True) -> int:
    """Paneli ATLAS profiliyle başlatır (profil = depo içi, makineden bağımsız)."""
    exe = root / "tools" / "juggler" / ("juggler.exe" if os.name == "nt" else "juggler")
    if not exe.is_file():
        _say(f"Panel ikilisi yok: {exe}")
        _say("docs/JUGGLER.md - kaynaktan derleyip tools/juggler/ altina koyun.")
        return 2
    env = {**os.environ, "JUGGLER_CONFIG_DIR": str(profile_sync.home_dir(root))}
    argv = [str(exe), "--port", str(port), "--project", str(root)]
    _say(f"Panel aciliyor: http://localhost:{port}/")
    if not wait:
        subprocess.Popen(argv, cwd=str(root), env=env)  # noqa: S603 - argv sabit
        return 0
    return subprocess.run(argv, cwd=str(root), env=env).returncode  # noqa: S603


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ATLAS baslat")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-panel", action="store_true", help="yalniz hazirla, paneli acma")
    ap.add_argument("--force-relocate", action="store_true", help="degismemis olsa da uyarla")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    _say(f"ATLAS - {root}")
    prepare(root, force_relocate=args.force_relocate)
    if args.no_panel:
        return 0
    _say()
    return launch_panel(root, args.port)


if __name__ == "__main__":
    sys.exit(main())

"""Çok-platform taşınabilir bundle üreticisi (yalnız stdlib).

Her hedef için `dist/atlas-<hedef>/` altında BAĞIMSIZ bir ağaç üretir:
  - runtime/python.tar.gz : python-build-standalone yorumlayıcısı (o platforma)
  - vendor/wheels/        : o platforma özel offline wheel deposu
  - src/, docs/, pyproject.toml, DECISIONS.md, CHANGELOG.md
  - başlatıcılar (atlas / atlas-sections) + setup-portable (offline kurulum)

Tasarım: yorumlayıcı arşivi host'ta AÇILMAZ (Windows'ta yabancı platform
arşivini açmak çok yavaş). Arşiv olduğu gibi kopyalanır; hedef makinede
`setup-portable` kendi OS'unda native `tar` ile açar (hızlı) + venv + offline
pip. Böylece build platform-bağımsız ve hızlıdır.

Hedef makinede TEK adım (offline; tar + venv + pip):  setup-portable.{cmd|sh}
Sonra:  atlas-sections i --h 1000 ...

Kullanım (bakımcı, internet gerekir):
  python tools/make_portable.py                 # tüm hedefler
  python tools/make_portable.py --targets linux-x86_64 windows-x86_64
  python tools/make_portable.py --list

Not: AI çekirdek (Claude Code CLI) bundle'a dahil DEĞİLDİR (bilinçli istisna,
bkz docs/OFFLINE.md). Yalnız hesap + platform CLI'ları paketlenir.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# --- Sürüm sabitleri (güncellemek için burayı değiştir) ---
PY_VERSION = "3.12.13"
PBS_TAG = "20260718"  # astral-sh/python-build-standalone release etiketi
PBS_BASE = (
    "https://github.com/astral-sh/python-build-standalone/releases/download/"
    f"{PBS_TAG}/"
)
RUNTIME_DEPS = ("numpy", "ezdxf", "pyyaml")
APP_ITEMS = ("src", "docs", "pyproject.toml", "README.md", "DECISIONS.md", "CHANGELOG.md")

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / ".cache"
DIST = ROOT / "dist"


@dataclass(frozen=True)
class Target:
    name: str
    triple: str              # python-build-standalone hedef üçlüsü
    pip_platforms: tuple[str, ...]  # pip download --platform değerleri
    os: str                  # "windows" | "unix"

    @property
    def archive(self) -> str:
        return f"cpython-{PY_VERSION}+{PBS_TAG}-{self.triple}-install_only.tar.gz"

    @property
    def url(self) -> str:
        return PBS_BASE + self.archive


TARGETS: dict[str, Target] = {
    t.name: t
    for t in (
        Target(
            "windows-x86_64", "x86_64-pc-windows-msvc", ("win_amd64",), "windows",
        ),
        Target(
            "linux-x86_64", "x86_64-unknown-linux-gnu",
            ("manylinux2014_x86_64", "manylinux_2_17_x86_64", "manylinux_2_28_x86_64"),
            "unix",
        ),
        Target(
            "macos-aarch64", "aarch64-apple-darwin", ("macosx_11_0_arm64",), "unix",
        ),
        Target(
            "macos-x86_64", "x86_64-apple-darwin",
            ("macosx_10_12_x86_64", "macosx_11_0_x86_64"), "unix",
        ),
    )
}


def _download(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"    önbellek: {dest.name}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"    indiriliyor: {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url) as r, tmp.open("wb") as f:  # noqa: S310
        shutil.copyfileobj(r, f)
    tmp.replace(dest)
    return dest


def _fetch_python(t: Target, bundle: Path) -> None:
    archive = _download(t.url, CACHE / t.archive)
    runtime = bundle / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    # Host'ta AÇMA — arşivi olduğu gibi kopyala; hedefte native tar açar.
    print("    kopyalanıyor: runtime/python.tar.gz")
    shutil.copy2(archive, runtime / "python.tar.gz")


def _fetch_wheels(t: Target, bundle: Path) -> None:
    wheels = bundle / "vendor" / "wheels"
    wheels.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "pip", "download",
        "--dest", str(wheels),
        "--only-binary=:all:",
        "--python-version", "3.12",
        "--implementation", "cp",
        "--abi", "cp312",
    ]
    for plat in t.pip_platforms:
        cmd += ["--platform", plat]
    cmd += list(RUNTIME_DEPS)
    print(f"    wheelhouse: {', '.join(t.pip_platforms)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stdout + res.stderr)
        raise SystemExit(f"[HATA] wheel indirme başarısız: {t.name}")


def _copy_app(bundle: Path) -> None:
    for item in APP_ITEMS:
        src = ROOT / item
        if not src.exists():
            continue
        dst = bundle / item
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(
                                "__pycache__", "*.pyc", "*.egg-info"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


_WIN_LAUNCHER = """\
@echo off
setlocal
set "ATLAS_HOME=%~dp0"
set "PYTHONPATH=%ATLAS_HOME%src"
set "PYTHONUTF8=1"
"%ATLAS_HOME%runtime\\venv\\Scripts\\python.exe" -m {mod} %*
"""

_WIN_SETUP = """\
@echo off
rem OFFLINE kurulum — internet GEREKMEZ. Bir kez calistir.
rem tar (Windows 10+ bsdtar) ve gomulu arsiv disinda hicbir sey gerektirmez.
setlocal
set "H=%~dp0"
set "PY=%H%runtime\\python\\python.exe"
if not exist "%PY%" (
  echo Yorumlayici aciliyor: runtime\\python.tar.gz
  tar -xzf "%H%runtime\\python.tar.gz" -C "%H%runtime" || (
    echo [HATA] tar basarisiz. Windows 10+ gerekir. & exit /b 1 )
)
echo Venv olusturuluyor...
"%PY%" -m venv "%H%runtime\\venv" || exit /b 1
echo Bagimliliklar OFFLINE kuruluyor...
"%H%runtime\\venv\\Scripts\\python.exe" -m pip install --no-index ^
  --find-links "%H%vendor\\wheels" {deps} || exit /b 1
echo Tamam. Dene: atlas-sections i --h 1000 --b 300 --tw 12 --tf 20
"""

_UNIX_LAUNCHER = """\
#!/usr/bin/env bash
set -euo pipefail
H="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
export PYTHONPATH="$H/src"
export PYTHONUTF8=1
exec "$H/runtime/venv/bin/python" -m {mod} "$@"
"""

_UNIX_SETUP = """\
#!/usr/bin/env bash
# OFFLINE kurulum — internet GEREKMEZ. Bir kez calistir.
set -euo pipefail
H="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PY="$H/runtime/python/bin/python3"
if [ ! -x "$PY" ]; then
  echo "Yorumlayici aciliyor: runtime/python.tar.gz"
  tar -xzf "$H/runtime/python.tar.gz" -C "$H/runtime"
fi
echo "Venv olusturuluyor..."
"$PY" -m venv "$H/runtime/venv"
echo "Bagimliliklar OFFLINE kuruluyor..."
"$H/runtime/venv/bin/python" -m pip install --no-index \\
  --find-links "$H/vendor/wheels" {deps}
echo "Tamam. Dene: ./atlas-sections i --h 1000 --b 300 --tw 12 --tf 20"
"""


def _write_scripts(t: Target, bundle: Path) -> None:
    deps = " ".join(RUNTIME_DEPS)
    if t.os == "windows":
        (bundle / "atlas.cmd").write_text(
            _WIN_LAUNCHER.format(mod="atlas_core.cli"), encoding="utf-8")
        (bundle / "atlas-sections.cmd").write_text(
            _WIN_LAUNCHER.format(mod="sections.cli"), encoding="utf-8")
        (bundle / "setup-portable.cmd").write_text(
            _WIN_SETUP.format(deps=deps), encoding="utf-8")
    else:
        for fn, mod in (("atlas", "atlas_core.cli"), ("atlas-sections", "sections.cli")):
            p = bundle / fn
            p.write_text(_UNIX_LAUNCHER.format(mod=mod), encoding="utf-8", newline="\n")
            p.chmod(0o755)
        sp = bundle / "setup-portable.sh"
        sp.write_text(_UNIX_SETUP.format(deps=deps), encoding="utf-8", newline="\n")
        sp.chmod(0o755)


def build(t: Target) -> Path:
    bundle = DIST / f"atlas-{t.name}"
    print(f"[{t.name}] -> {bundle.relative_to(ROOT)}")
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)
    _fetch_python(t, bundle)
    _fetch_wheels(t, bundle)
    _copy_app(bundle)
    _write_scripts(t, bundle)
    print(f"    hazır: {bundle.relative_to(ROOT)}")
    return bundle


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--targets", nargs="+", choices=list(TARGETS),
                    help="Üretilecek hedefler (varsayılan: hepsi)")
    ap.add_argument("--list", action="store_true", help="Hedefleri listele")
    args = ap.parse_args(argv)

    if args.list:
        for name, t in TARGETS.items():
            print(f"{name:16s} {t.triple}  py{PY_VERSION}")
        return 0

    names = args.targets or list(TARGETS)
    print(f"Python {PY_VERSION} (pbs {PBS_TAG}) | hedefler: {', '.join(names)}\n")
    for name in names:
        build(TARGETS[name])
    print(f"\nBitti. Bundle'lar: {DIST.relative_to(ROOT)}/")
    print("Hedef makinede: setup-portable.{cmd|sh} -> atlas-sections ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

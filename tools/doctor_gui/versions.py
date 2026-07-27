"""Sürüm tespiti: yerelde ne kurulu, üstakımda ne var (yalnız stdlib).

Bu modül "güncelleme var mı" sorusunu yanıtlar. İki yarısı vardır:

* **yerel** — dosya sisteminden okunur (package.json, dist-info, `--version`).
  İnternet gerekmez, her zaman çalışır.
* **uzak** — npm/PyPI/GitHub kayıt defterlerinden okunur. İnternet yoksa
  sessizce `None` döner; sağlık taraması bu yüzden ASLA durmaz — güncelleme
  bilgisi eksik kalır, kurulum denetimi tam yapılır.

Uzak sorgular kısa süre (varsayılan 6 sn) bekler ve süreç ömrü boyunca
önbelleklenir; tarama tekrarlandığında ağ yeniden dövülmez.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from tools.setup_gui.detect import IS_WIN, _exe, project_root

NET_TIMEOUT = 6.0
_REMOTE_CACHE: dict[str, str | None] = {}

# Sürüm dizgesinden sayısal çekirdeği ayıklar: "juggler v0.4.2 (commit: ...)" → 0.4.2
# Baş/son sınır için \b KULLANILMAZ: "v0.4.2"de 'v' ile '0' arasında sınır yoktur
# (ikisi de kelime karakteri) ve sürüm hiç yakalanmazdı. Bunun yerine "önünde
# rakam/nokta olmasın" koşulu aranır.
_SEMVER_RE = re.compile(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?(?![\d])")


def parse_semver(text: str | None) -> tuple[int, int, int] | None:
    """Serbest metinden ilk semver üçlüsünü çıkarır (yoksa None)."""
    if not text:
        return None
    m = _SEMVER_RE.search(text)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def is_outdated(local: str | None, latest: str | None) -> bool:
    """Yalnız GÜVENİLİR biçimde eskiyse True.

    Biri okunamadıysa veya semver'e benzemiyorsa False döner — "bilinmiyor"u
    "eski" diye raporlamak kullanıcıyı gereksiz güncellemeye iter.
    """
    a, b = parse_semver(local), parse_semver(latest)
    return bool(a and b and a < b)


# --- yerel --------------------------------------------------------------------


def _run_version(argv: list[str], timeout: float = 20.0) -> str | None:
    try:
        out = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    blob = (out.stdout or "") + (out.stderr or "")
    line = next((ln.strip() for ln in blob.splitlines() if ln.strip()), "")
    return line or None


def _pkg_json_version(pkg_dir: Path) -> str | None:
    """node_modules/<paket>/package.json içindeki sürüm."""
    f = pkg_dir / "package.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("version")
    except (OSError, json.JSONDecodeError):
        return None


def _dist_info_version(site_packages: Path, dist: str) -> str | None:
    """py-venv içindeki bir pip paketinin sürümü (<ad>-<sürüm>.dist-info)."""
    if not site_packages.is_dir():
        return None
    prefix = dist.replace("-", "_").lower()
    for d in site_packages.glob("*.dist-info"):
        name = d.name.lower()
        if name.startswith(prefix + "-"):
            return d.name[len(prefix) + 1 : -len(".dist-info")]
    return None


def _site_packages(root: Path) -> Path:
    venv = root / "tools" / "ai-cli" / "py-venv"
    return venv / ("Lib" if IS_WIN else "lib") / "site-packages"


def local_versions(root: Path | None = None) -> dict[str, str | None]:
    """Projenin kullandığı her bileşenin YEREL sürümü (kurulu değilse None)."""
    root = root or project_root()
    nm = root / "tools" / "ai-cli" / "node_modules"
    juggler = root / "tools" / "juggler" / _exe("juggler")
    goose = root / "tools" / "goose" / "goose-package" / _exe("goose")
    ollama = root / "tools" / "ollama" / _exe("ollama")

    return {
        "juggler": _run_version([str(juggler), "--version"]) if juggler.is_file() else None,
        "opencode": _pkg_json_version(nm / "opencode-ai"),
        "kilo": _pkg_json_version(nm / "@kilocode" / "cli"),
        "cline": _pkg_json_version(nm / "cline"),
        "kimi": _dist_info_version(_site_packages(root), "kimi-cli"),
        "goose": _run_version([str(goose), "--version"]) if goose.is_file() else None,
        "ollama": _run_version([str(ollama), "--version"]) if ollama.is_file() else None,
    }


# --- uzak ---------------------------------------------------------------------


def _get_json(url: str, timeout: float = NET_TIMEOUT) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "ATLAS-doctor"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - sabit https
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return None


def npm_latest(pkg: str) -> str | None:
    doc = _get_json(f"https://registry.npmjs.org/{pkg}/latest")
    return (doc or {}).get("version")


def pypi_latest(pkg: str) -> str | None:
    doc = _get_json(f"https://pypi.org/pypi/{pkg}/json")
    return ((doc or {}).get("info") or {}).get("version")


def github_latest(repo: str) -> str | None:
    doc = _get_json(f"https://api.github.com/repos/{repo}/releases/latest")
    tag = (doc or {}).get("tag_name")
    return tag.lstrip("v") if isinstance(tag, str) else None


# Bileşen → uzak kayıt defteri. Ollama kasten yok: taşınabilir kurulumu
# sihirbaz yönetir, sürümü ajanların bağlantısını etkilemez.
REMOTE_SOURCES: dict[str, tuple[str, str]] = {
    "juggler": ("github", "juggler-ai/juggler"),
    "opencode": ("npm", "opencode-ai"),
    "kilo": ("npm", "@kilocode/cli"),
    "cline": ("npm", "cline"),
    "kimi": ("pypi", "kimi-cli"),
    "goose": ("github", "block/goose"),
}


def remote_latest(component: str) -> str | None:
    """Bir bileşenin üstakımdaki son sürümü (ağ yoksa None). Önbellekli."""
    if component in _REMOTE_CACHE:
        return _REMOTE_CACHE[component]
    src = REMOTE_SOURCES.get(component)
    value = None
    if src:
        kind, name = src
        value = {"npm": npm_latest, "pypi": pypi_latest, "github": github_latest}[kind](name)
    _REMOTE_CACHE[component] = value
    return value


def clear_cache() -> None:
    """Önbelleği boşaltır (kullanıcı 'yeniden denetle' derse ağ yeniden sorulur)."""
    _REMOTE_CACHE.clear()


def online() -> bool:
    """Kayıt defterlerine erişilebiliyor mu (tek ucuz sorgu)."""
    return _get_json("https://registry.npmjs.org/cline/latest", timeout=4.0) is not None

"""Taşınabilir node ve git-bash'i depo içine indirir (yalnız stdlib).

NEDEN: iki ajan (kilo, cline) node ister, kimi git-bash ister. Bu makinede
ikisi de kullanıcı dizinine kurulu (`%LOCALAPPDATA%\\hermes\\node`,
`%LOCALAPPDATA%\\Programs\\Git`) ve sarmalayıcılara MUTLAK yolla yazılıyordu —
klasörü başka bir bilgisayara taşıyınca o yollar yok, ajanlar ölür. Çözüm:
ikisini de `tools/node` ve `tools/git` altına al; sarmalayıcılar `%ROOT%`
göreli yazsın.

Arşivler Python `zipfile` ile açılır: ÖLÇÜLDÜ (2026-07-24, goose zip'i) —
bsdtar/PowerShell büyük zip'lerde bozuk çıktı verebiliyor, `zipfile` vermedi.

Kullanım (internet gerekir, bir kez):
    python -m tools.portable.vendor            # eksikleri indir
    python -m tools.portable.vendor --force    # yeniden indir
"""

from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

NODE_INDEX = "https://nodejs.org/dist/index.json"
GIT_RELEASE_API = "https://api.github.com/repos/git-for-windows/git/releases/latest"
UA = {"User-Agent": "ATLAS-portable-vendor"}


def node_dir(root: Path) -> Path:
    return root / "tools" / "node"


def git_dir(root: Path) -> Path:
    return root / "tools" / "git"


def _get(url: str, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - sabit https
        return resp.read()


def _download(url: str, dst: Path, timeout: float = 900.0) -> Path:
    """İndirmeyi ÖNCE .part'a yazar, bitince adlandırır — yarım dosya bırakmaz."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_suffix(dst.suffix + ".part")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp, part.open("wb") as out:  # noqa: S310
        shutil.copyfileobj(resp, out, length=1 << 20)
    part.replace(dst)
    return dst


def _unzip_flat(archive: Path, dst: Path, strip_top: bool = True) -> None:
    """Zip'i doğrudan `dst`e açar; `strip_top` ise arşivin tek kök klasörünü atar.

    Ara klasöre açıp yeniden ADLANDIRMAK yerine doğrudan hedefe yazıyoruz:
    ÖLÇÜLDÜ (2026-07-28, MinGit) — Windows'ta taze açılmış bir dizini yeniden
    adlandırmak `PermissionError [WinError 5]` veriyor (Defender henüz dosyaları
    tarıyor, tanıtıcılar açık). Doğrudan yazmada bu adım hiç yok.
    """
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    with zipfile.ZipFile(archive) as zf:
        prefix = ""
        if strip_top:
            tops = {n.split("/", 1)[0] for n in zf.namelist() if n.strip()}
            if len(tops) == 1:
                prefix = tops.pop() + "/"
        for info in zf.infolist():
            name = info.filename
            rel = name[len(prefix) :] if prefix and name.startswith(prefix) else name
            if not rel:
                continue
            target = dst / rel
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out, length=1 << 20)


def latest_node_lts() -> tuple[str, str]:
    """(sürüm, zip URL'si) — en yeni LTS, windows x64."""
    doc = json.loads(_get(NODE_INDEX).decode("utf-8"))
    for rel in doc:
        if rel.get("lts") and "win-x64-zip" in (rel.get("files") or []):
            v = rel["version"]
            return v, f"https://nodejs.org/dist/{v}/node-{v}-win-x64.zip"
    raise RuntimeError("node LTS bulunamadı")


def latest_mingit() -> tuple[str, str]:
    """(sürüm, zip URL'si) — MinGit 64-bit (busybox DEĞİL: bash.exe şart)."""
    doc = json.loads(_get(GIT_RELEASE_API).decode("utf-8"))
    for asset in doc.get("assets", []):
        name = asset.get("name", "")
        if name.startswith("MinGit-") and name.endswith("-64-bit.zip") and "busybox" not in name:
            return doc.get("tag_name", "?"), asset["browser_download_url"]
    raise RuntimeError("MinGit 64-bit varlığı bulunamadı")


def ensure_node(root: Path, force: bool = False) -> dict:
    exe = node_dir(root) / "node.exe"
    if exe.is_file() and not force:
        return {"ok": True, "detail": f"node zaten var: {exe}", "skipped": True}
    version, url = latest_node_lts()
    cache = root / "tools" / ".cache" / f"node-{version}-win-x64.zip"
    if not cache.is_file() or force:
        _download(url, cache)
    _unzip_flat(cache, node_dir(root))
    if not exe.is_file():
        return {"ok": False, "detail": f"node.exe açılan arşivde yok: {node_dir(root)}"}
    return {"ok": True, "detail": f"node {version} → {node_dir(root)}", "version": version}


def ensure_git(root: Path, force: bool = False) -> dict:
    d = git_dir(root)
    if _bundled_bash(d) and not force:
        return {"ok": True, "detail": f"git-bash zaten var: {d}", "skipped": True}
    version, url = latest_mingit()
    cache = root / "tools" / ".cache" / f"MinGit-{version}-64-bit.zip"
    if not cache.is_file() or force:
        _download(url, cache)
    # MinGit arşivi köksüzdür (cmd/, mingw64/, usr/ doğrudan) — strip etme.
    _unzip_flat(cache, d, strip_top=False)
    _ensure_bash_name(d)
    bash = _bundled_bash(d)
    if not bash:
        return {"ok": False, "detail": f"bash.exe açılan arşivde yok: {d}"}
    return {"ok": True, "detail": f"git {version} → {bash}", "version": version}


def _ensure_bash_name(d: Path) -> Path | None:
    """MinGit `bash.exe` adını taşımaz — `sh.exe` AYNI ikilidir, kopyala.

    ÖLÇÜLDÜ (2026-07-28): kurulu Git for Windows'ta `usr/bin/sh.exe` ile
    `usr/bin/bash.exe` sha256 olarak BİREBİR aynı dosyadır; bash çalışma kipini
    argv[0]'dan seçer. MinGit yalnız `sh.exe` gönderiyor; kimi ise yolunda
    "bash" arayacağı için kopyayı `bash.exe` adıyla koyuyoruz — yeniden
    adlandırmıyoruz ki `sh.exe` bekleyen başka bir şey kırılmasın.
    """
    if (existing := _bundled_bash(d)) is not None:
        return existing
    sh = d / "usr" / "bin" / "sh.exe"
    if not sh.is_file():
        return None
    target = d / "usr" / "bin" / "bash.exe"
    shutil.copy2(sh, target)
    return target


def _bundled_bash(d: Path) -> Path | None:
    """MinGit'te bash `bin/` veya `usr/bin/` altında olabilir; ikisini de dene."""
    for rel in ("bin/bash.exe", "usr/bin/bash.exe"):
        p = d / rel
        if p.is_file():
            return p
    return None


def ensure_all(root: Path, force: bool = False) -> list[dict]:
    return [ensure_node(root, force), ensure_git(root, force)]


def main() -> int:
    ap = argparse.ArgumentParser(description="Taşınabilir node + git-bash indir")
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--force", action="store_true", help="mevcut olsa da yeniden indir")
    args = ap.parse_args()
    rc = 0
    for res in ensure_all(args.root, args.force):
        print(("OK  " if res["ok"] else "HATA") + "  " + res["detail"])
        rc = rc or (0 if res["ok"] else 1)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

"""node / git-bash çözümü — ÖNCE depo içi, sonra makine.

Sarmalayıcı üreticisi ve ajan sözleşmesi bu modülü kullanır. Sıra kasıtlı:
depo içindeki kopya kazanır, çünkü klasör başka bir bilgisayara taşındığında
ayakta kalan tek şey odur. Makinedeki kurulum yalnız yedek çaredir (geliştirme
makinesi, henüz vendor edilmemiş depo).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

NODE_REL = ("tools", "node", "node.exe")
# MinGit'te bash `bin/`, tam Git kurulumunda da `bin/` altındadır; `usr/bin`
# bazı paketlerde tek konumdur — ikisi de denenir.
BASH_RELS = (("tools", "git", "bin", "bash.exe"), ("tools", "git", "usr", "bin", "bash.exe"))


def bundled_node(root: Path) -> Path | None:
    p = root.joinpath(*NODE_REL)
    return p if p.is_file() else None


def bundled_bash(root: Path) -> Path | None:
    for rel in BASH_RELS:
        p = root.joinpath(*rel)
        if p.is_file():
            return p
    return None


def node_exe(root: Path | None = None) -> str:
    """Çalıştırılacak node. Depo içi kopya varsa O kullanılır."""
    if root and (p := bundled_node(root)):
        return str(p)
    return shutil.which("node") or "node"


def npm_cmd(root: Path | None = None) -> str | None:
    """npm (yoksa None). Depo içi node paketi npm'i de getirir — güncellemeler
    yeni bir makinede de çalışsın diye önce o aranır."""
    if root:
        p = node_dir(root) / "npm.cmd"
        if p.is_file():
            return str(p)
    return shutil.which("npm")


def node_dir(root: Path) -> Path:
    return root / "tools" / "node"


def git_bash(root: Path | None = None) -> Path | None:
    """Git for Windows `bash.exe` (yoksa None).

    kimi-cli'nin Shell aracı bunu ister ve HER OTURUM AÇILIŞINDA yeniden arar:
    `where.exe git` → `git --exec-path` (5 sn zaman aşımı) → yalnız
    `C:\\Program Files\\Git\\...`. ÖLÇÜLDÜ (2026-07-28): git kullanıcı dizinine
    kurulu olduğunda bu arama arada bir düşüyor ve `session/new` "Internal error"
    veriyor. Yolu bir kez çözüp `KIMI_CLI_GIT_BASH_PATH` ile sabitliyoruz.
    """
    if root and (p := bundled_bash(root)):
        return p
    candidates: list[Path] = []
    if override := os.environ.get("KIMI_CLI_GIT_BASH_PATH"):
        candidates.append(Path(override))
    if git := shutil.which("git"):
        # git.exe ya <git>\cmd\ ya da <git>\mingw64\bin\ altındadır.
        parent = Path(git).parent.parent
        candidates += [parent / "bin" / "bash.exe", parent.parent / "bin" / "bash.exe"]
    candidates += [
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files (x86)\Git\bin\bash.exe"),
    ]
    for c in candidates:
        # Sarmalayıcılar saf ASCII yazılır; ASCII olmayan yol yazılamaz.
        if str(c).isascii() and c.is_file():
            return c
    return None


def report(root: Path) -> list[dict]:
    """Taşınabilirlik özeti: her çalışma zamanı nereden geliyor?"""
    node = bundled_node(root)
    bash = bundled_bash(root)
    return [
        {
            "name": "node",
            "portable": bool(node),
            "path": str(node or shutil.which("node") or ""),
            "needed_by": "kilo, cline",
        },
        {
            "name": "git-bash",
            "portable": bool(bash),
            "path": str(bash or (git_bash(root) or "")),
            "needed_by": "kimi (Shell aracı)",
        },
    ]

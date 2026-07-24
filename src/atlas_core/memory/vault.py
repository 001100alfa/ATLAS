"""ATLAS Beyin: Obsidian-uyumlu vault üzerinde bilgi grafı.

Notlar düz Markdown + [[wikilink]] — Obsidian'da doğrudan açılır.
Graf, linklerden türetilir: ekstra veritabanı yok, tek gerçek kaynak vault.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
TAG = re.compile(r"(?<!\S)#([\w/çğıöşüÇĞİÖŞÜ-]+)")


class VaultError(RuntimeError):
    """Vault işlem hatası."""


@dataclass(frozen=True, slots=True)
class Note:
    """Vault'taki tek not."""

    name: str          # dosya adı (uzantısız) = graf düğüm kimliği
    path: Path
    links: tuple[str, ...]   # [[hedef]] listesi
    tags: tuple[str, ...]


@dataclass(slots=True)
class Graph:
    """Wikilink'lerden türetilmiş yönlü graf."""

    nodes: dict[str, Note] = field(default_factory=dict)

    def backlinks(self, name: str) -> list[str]:
        """`name`'e link veren notlar (Obsidian backlink eşleniği)."""
        return sorted(n.name for n in self.nodes.values() if name in n.links)

    def orphans(self) -> list[str]:
        """Ne link veren ne alan notlar — bakım sinyali."""
        linked: set[str] = set()
        for n in self.nodes.values():
            linked.update(n.links)
        return sorted(
            n.name for n in self.nodes.values()
            if not n.links and n.name not in linked
        )

    def neighbors(self, name: str, depth: int = 1) -> set[str]:
        """`name` çevresindeki bağlam (her iki yönde, `depth` adım)."""
        if name not in self.nodes:
            return set()
        frontier, seen = {name}, {name}
        for _ in range(depth):
            nxt: set[str] = set()
            for cur in frontier:
                if cur in self.nodes:
                    nxt.update(self.nodes[cur].links)
                nxt.update(self.backlinks(cur))
            nxt -= seen
            seen |= nxt
            frontier = nxt
        seen.discard(name)
        return seen


class Vault:
    """Obsidian-uyumlu Markdown vault sürücüsü."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str, folder: str = "") -> Path:
        if "/" in name or "\\" in name or name.startswith("."):
            raise VaultError(f"Geçersiz not adı: {name!r}")
        d = self.root / folder if folder else self.root
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{name}.md"

    def write(self, name: str, content: str, folder: str = "") -> Path:
        p = self._path(name, folder)
        p.write_text(content, encoding="utf-8")
        return p

    def append(self, name: str, content: str, folder: str = "") -> Path:
        p = self._path(name, folder)
        old = p.read_text(encoding="utf-8") if p.exists() else ""
        p.write_text(old + content, encoding="utf-8")
        return p

    def read(self, name: str, folder: str = "") -> str:
        p = self._path(name, folder)
        if not p.exists():
            raise VaultError(f"Not bulunamadı: {name}")
        return p.read_text(encoding="utf-8")

    def daily(self, entry: str, day: date | None = None) -> Path:
        """Günlük nota (Obsidian daily-note deseni) kayıt düşer."""
        d = (day or date.today()).isoformat()
        return self.append(d, f"- {entry}\n", folder="daily")

    def graph(self) -> Graph:
        """Tüm vault'u tarayıp wikilink grafını türetir."""
        g = Graph()
        for p in sorted(self.root.rglob("*.md")):
            text = p.read_text(encoding="utf-8")
            g.nodes[p.stem] = Note(
                name=p.stem,
                path=p,
                links=tuple(dict.fromkeys(WIKILINK.findall(text))),
                tags=tuple(dict.fromkeys(TAG.findall(text))),
            )
        return g

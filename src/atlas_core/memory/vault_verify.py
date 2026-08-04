"""SPEC 042: Vault graf sağlığı doğrulaması.

Vault (Obsidian-uyumlu Markdown) üzerinde kalite sinyalleri üretir:
kırık `[[wikilink]]`, orfan not (linkli değil + link vermez), tek-notta
kullanılan (orfan) `#tag`.

Modül `Vault.graph()` çıktısı üzerinde çalışır; vault üzerinde
YAZMA YOK — salt-okunur analiz. Yan etkisi yok.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC

from atlas_core.memory.vault import Graph


@dataclass(frozen=True, slots=True)
class BrokenLink:
    """`from` notu, `to` hedefine link veriyor ama hedef vault'ta yok."""

    frm: str  # 'from' Python rezerve — 'frm' seçildi
    to: str


@dataclass(slots=True)
class VerifyReport:
    """SPEC 042: Vault graf doğrulama raporu.

    - `broken_links` : hedef notu vault'ta olmayan wikilink'ler
      (deterministik sıralı: `(frm, to)` sözlük sırası).
    - `orphan_notes` : ne link veren ne link alan notlar (bakım sinyali).
    - `orphan_tags`  : yalnızca **bir** notta geçen tag'ler.
    - `notes_total`, `links_total`, `tags_total` : sayaçlar.
    """

    broken_links: list[BrokenLink] = field(default_factory=list)
    orphan_notes: list[str] = field(default_factory=list)
    orphan_tags: list[str] = field(default_factory=list)
    notes_total: int = 0
    links_total: int = 0
    tags_total: int = 0

    @property
    def is_clean(self) -> bool:
        """Hiçbir bulgu yoksa `True` (`--strict` için gate)."""
        return (
            not self.broken_links
            and not self.orphan_notes
            and not self.orphan_tags
        )

    def to_dict(self) -> dict[str, object]:
        """Sözlük gösterimi (JSON serileştirme için)."""
        return {
            "broken_links": [
                {"from": b.frm, "to": b.to} for b in self.broken_links
            ],
            "orphan_notes": list(self.orphan_notes),
            "orphan_tags": list(self.orphan_tags),
            "notes_total": self.notes_total,
            "links_total": self.links_total,
            "tags_total": self.tags_total,
            "is_clean": self.is_clean,
        }


def format_report_markdown(report: VerifyReport, vault_root: str) -> str:
    """SPEC 052: `VerifyReport`'u insan-okunur Markdown'a çevir.

    Hook auto-dump çıktısı; `.atlas/vault-health.md` gibi git-ignored
    bir yola yazılır. Kullanıcı commit engellendiğinde ne düzelteceğini
    tek dosyadan görür.

    Format deterministik (broken_links + orphan_* zaten sıralı).
    Timestamp UTC ISO 8601 (deterministik kaynak).
    """
    from datetime import datetime

    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = [
        "# ATLAS vault verify raporu",
        "",
        f"- oluşturuldu: {ts}",
        f"- vault: `{vault_root}`",
        f"- notlar: {report.notes_total}",
        f"- linkler: {report.links_total}",
        f"- taglar: {report.tags_total}",
        f"- **durum: {'✔ temiz' if report.is_clean else '❌ bulgu var'}**",
        "",
    ]

    if report.broken_links:
        lines.append(f"## Kırık linkler ({len(report.broken_links)})")
        lines.append("")
        for b in report.broken_links:
            lines.append(f"- `{b.frm}` → `{b.to}`")
        lines.append("")

    if report.orphan_notes:
        lines.append(f"## Orfan notlar ({len(report.orphan_notes)})")
        lines.append("")
        lines.append("*Ne link veren ne link alan notlar — bakım sinyali.*")
        lines.append("")
        for n in report.orphan_notes:
            lines.append(f"- `{n}`")
        lines.append("")

    if report.orphan_tags:
        lines.append(f"## Orfan taglar ({len(report.orphan_tags)})")
        lines.append("")
        lines.append("*Yalnız bir notta geçen `#tag`'lar — sözlük gürültüsü.*")
        lines.append("")
        for t in report.orphan_tags:
            lines.append(f"- `#{t}`")
        lines.append("")

    if not report.is_clean:
        lines += [
            "## Öneri",
            "",
            "1. Kırık linkler → hedef notu oluştur veya link yolunu düzelt.",
            "2. Orfan notlar → başka bir notta `[[not-adı]]` ile bağla ya",
            "   da silmeye karar ver.",
            "3. Orfan taglar → tag'i başka notlarda da kullan ya da",
            "   yazımını düzelt.",
            "4. Ayrıntı için: `atlas vault verify` (renkli konsol çıktısı).",
            "",
        ]

    return "\n".join(lines).rstrip() + "\n"


def verify_graph(graph: Graph) -> VerifyReport:
    """SPEC 042: `Graph` üzerinden vault sağlık raporu üret.

    - Kırık link: `node.links` içindeki her hedef `graph.nodes` içinde
      yok ise kaydedilir. Sıralama (frm, to) sözlük sırası.
    - Orfan not: `Graph.orphans()` (ne link veren ne link alan).
    - Orfan tag: bütün notlarda toplandığında yalnızca bir kez geçen
      tag'ler (dağılım Counter ile hesaplanır).
    - Toplamlar: not sayısı; distinct-per-note link ve tag topları
      (`Vault.graph()` zaten `dict.fromkeys` ile tekilleştiriyor).
    """
    nodes = graph.nodes
    node_names = set(nodes.keys())

    broken: list[BrokenLink] = []
    links_total = 0
    tag_counter: Counter[str] = Counter()

    for name in sorted(nodes.keys()):
        note = nodes[name]
        links_total += len(note.links)
        for tag in note.tags:
            tag_counter[tag] += 1
        for target in note.links:
            if target not in node_names:
                broken.append(BrokenLink(frm=name, to=target))

    broken.sort(key=lambda b: (b.frm, b.to))

    orphan_tags = sorted(t for t, c in tag_counter.items() if c == 1)

    return VerifyReport(
        broken_links=broken,
        orphan_notes=graph.orphans(),
        orphan_tags=orphan_tags,
        notes_total=len(nodes),
        links_total=links_total,
        tags_total=sum(tag_counter.values()),
    )

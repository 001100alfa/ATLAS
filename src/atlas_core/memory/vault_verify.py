"""SPEC 042: Vault graf sağlığı doğrulaması.

Vault (Obsidian-uyumlu Markdown) üzerinde kalite sinyalleri üretir:
kırık `[[wikilink]]`, orfan not (linkli değil + link vermez), tek-notta
kullanılan (orfan) `#tag`.

Modül `Vault.graph()` çıktısı üzerinde çalışır; vault üzerinde
YAZMA YOK — salt-okunur analiz. Yan etkisi yok.
"""

from __future__ import annotations

import shutil
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC
from pathlib import Path

from atlas_core.memory.vault import Graph, Vault


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


# ═════════════════════════════════════════════════════════════════════
# SPEC 046: orfan not arşivleme
# ═════════════════════════════════════════════════════════════════════


@dataclass(slots=True, frozen=True)
class OrphanAction:
    """SPEC 046: tek bir orfan not için taşıma planı/sonucu.

    - `src`: kaynak `.md` yolu (vault kökünden çözümlenmiş)
    - `dst`: hedef yol (`_archive/orphans-YYYY-MM-DD/<name>.md` veya
      çakışma varsa `-N.md` suffix)
    - `action`: `"planned"` (dry-run) | `"moved"` (gerçek taşıma) |
      `"skipped"` (src yok — ör. verify sonrası silinmiş)
    """

    src: Path
    dst: Path
    action: str


def _find_orphan_paths(vault: Vault, orphan_names: list[str]) -> list[Path]:
    """SPEC 046: orfan not adlarını vault kökünde `.md` yollarına çöz.

    Not adları vault'ın rglob taramasından geldiği için hepsi vault
    içindedir; ancak alt-klasörde (`daily/`, `tasks/`) olabilirler.
    `Vault.graph()` `p.stem` kullanıyor → düz not adı; klasörü bulmak
    için `rglob(f"{name}.md")`.
    """
    root = vault.root
    resolved: list[Path] = []
    for name in orphan_names:
        matches = list(root.rglob(f"{name}.md"))
        if matches:
            # Aynı stem birden fazla klasörde olabilir; hepsini ekle
            resolved.extend(matches)
    return resolved


def _unique_dst(base: Path) -> Path:
    """SPEC 046: `base` mevcut ise `<stem>-1.md`, `-2.md` ... suffix.

    Sonsuz döngü koruması: 1000 denemede bulunamazsa raise
    `RuntimeError`. Pratikte gerçekleşmez (aynı isimde 1000 orfan
    imkânsız), ama defense-in-depth.
    """
    if not base.exists():
        return base
    stem = base.stem
    suffix = base.suffix
    parent = base.parent
    for n in range(1, 1001):
        candidate = parent / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"benzersiz hedef bulunamadı (>1000 çakışma): {base}")


@dataclass(slots=True, frozen=True)
class StubAction:
    """SPEC 058: tek bir kırık link için stub not oluşturma sonucu.

    - `target`: `<to>` hedefi (notun adı — link'in gösterdiği stem)
    - `path`: yazılan (veya planlanan) `.md` yolu
    - `sources`: bu hedefe link veren tüm `from` notları (birden fazla
      olabilir; stub içeriğinde referans listesi)
    - `action`: `"planned"` (dry-run) | `"created"` (yazıldı) |
      `"skipped"` (dosya zaten var, dokunulmadı)
    """

    target: str
    path: Path
    sources: tuple[str, ...]
    action: str


_STUB_TEMPLATE = """# {target}

#stub

Bu not `atlas vault fix-broken` tarafından otomatik oluşturuldu
(SPEC 058). Kaynağı doldur veya alakasız ise `atlas vault fix-orphans
--apply` ile temizle.

## Kırık link kaynağı ({n_sources})

{sources_list}

<!-- oluşturulma: {ts} -->
"""


def create_stub_notes(
    vault: Vault,
    broken_links: list[BrokenLink],
    target_dir: Path,
    *,
    dry_run: bool,
) -> list[StubAction]:
    """SPEC 058: `broken_links` içindeki her hedef `to` için stub not
    oluştur.

    - Aynı hedefe link veren birden fazla `from` varsa TEK stub üretilir;
      stub içeriğinde tüm kaynaklar listelenir.
    - Hedef adı (`to`) vault içinde zaten varsa (yarış durumu — verify
      sonrası oluşturulmuş) → `action="skipped"`, dokunulmaz.
    - `target_dir` yoksa `mkdir -p` (dry-run'da klasör oluşturulmaz).
    - Dry-run: dosya sistemi dokunulmaz.

    Döner: her hedef için StubAction listesi (hedef adı sözlük sırası).
    """
    from datetime import datetime

    # Aynı hedefe farklı `from`'lar → tekilleştir + kaynak topla
    targets: dict[str, list[str]] = {}
    for bl in broken_links:
        targets.setdefault(bl.to, []).append(bl.frm)

    actions: list[StubAction] = []
    if not dry_run and targets:
        target_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    for name in sorted(targets):
        sources = tuple(sorted(set(targets[name])))
        # Vault'ta not zaten var mı? (verify sonrası oluşmuş olabilir)
        if list(vault.root.rglob(f"{name}.md")):
            actions.append(StubAction(
                target=name,
                path=target_dir / f"{name}.md",
                sources=sources,
                action="skipped",
            ))
            continue

        dst = target_dir / f"{name}.md"
        if dry_run:
            actions.append(StubAction(
                target=name, path=dst, sources=sources, action="planned",
            ))
            continue

        sources_list = "\n".join(f"- `[[{s}]]`" for s in sources)
        content = _STUB_TEMPLATE.format(
            target=name,
            n_sources=len(sources),
            sources_list=sources_list,
            ts=ts,
        )
        dst.write_text(content, encoding="utf-8")
        actions.append(StubAction(
            target=name, path=dst, sources=sources, action="created",
        ))

    return actions


def archive_orphan_notes(
    vault: Vault,
    orphan_names: list[str],
    target_dir: Path,
    *,
    dry_run: bool,
) -> list[OrphanAction]:
    """SPEC 046: `orphan_names` içindeki notları `target_dir`'e taşı.

    - `target_dir` yoksa `mkdir -p` (dry-run'da da klasör oluşturulmaz —
      salt-okunur).
    - Her not için hedef: `target_dir/<name>.md`; çakışma → `-N.md`.
    - `dry_run=True` → dosya sistemi dokunulmaz; `OrphanAction(action=
      "planned")` üretilir.
    - `dry_run=False` → `shutil.move` ile atomik taşıma (aynı FS içinde
      rename; farklı FS'de copy+delete). Kaynak yok → `action="skipped"`.

    Döner: her not için OrphanAction listesi (kararlı sıralı — girdi
    sırası korunur). Hata durumunda bile başlanan işlemlerin sonucu
    döner (kısmi ilerleme).
    """
    paths = _find_orphan_paths(vault, orphan_names)
    actions: list[OrphanAction] = []

    if not dry_run and paths:
        target_dir.mkdir(parents=True, exist_ok=True)

    for src in paths:
        if not src.is_file():
            # verify ile fix arasında silinmiş olabilir — nazikçe atla
            actions.append(OrphanAction(
                src=src, dst=target_dir / src.name, action="skipped",
            ))
            continue
        dst = _unique_dst(target_dir / src.name)
        if dry_run:
            actions.append(OrphanAction(src=src, dst=dst, action="planned"))
        else:
            shutil.move(str(src), str(dst))
            actions.append(OrphanAction(src=src, dst=dst, action="moved"))
    return actions


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

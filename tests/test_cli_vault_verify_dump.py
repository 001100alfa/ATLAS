"""SPEC 052 — atlas vault verify --dump-report + format_report_markdown."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault import Vault
from atlas_core.memory.vault_verify import (
    VerifyReport,
    format_report_markdown,
    verify_graph,
)


def _make_vault(root: Path, notes: dict[str, str]) -> Vault:
    root.mkdir(parents=True, exist_ok=True)
    for name, content in notes.items():
        (root / f"{name}.md").write_text(content, encoding="utf-8")
    return Vault(root)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


# ═════════════════════════════════════════════════════════════════════
# format_report_markdown (birim)
# ═════════════════════════════════════════════════════════════════════


def test_052_format_temiz_vault() -> None:
    """Temiz vault → başlık + `durum: temiz` satırı; öneri bölümü YOK."""
    rep = VerifyReport(notes_total=3, links_total=4, tags_total=2)
    md = format_report_markdown(rep, "vault")
    assert "# ATLAS vault verify raporu" in md
    assert "durum: ✔ temiz" in md
    assert "## Öneri" not in md
    assert "notlar: 3" in md
    assert "vault: `vault`" in md


def test_052_format_bulguli_vault_tum_bolumleri_basar(tmp_path: Path) -> None:
    """Kırık link + orfan not + orfan tag → 3 bölüm + Öneri."""
    v = _make_vault(tmp_path / "v", {
        "a": "[[yok]] #tek",
        "b": "[[a]] #ortak",
        "c": "[[a]] #ortak",
        "yalniz": "hiç link yok",
    })
    rep = verify_graph(v.graph())
    md = format_report_markdown(rep, str(v))
    assert "## Kırık linkler (1)" in md
    assert "`a` → `yok`" in md
    assert "## Orfan notlar (1)" in md
    assert "`yalniz`" in md
    assert "## Orfan taglar (1)" in md
    assert "`#tek`" in md
    assert "## Öneri" in md
    assert "durum: ❌ bulgu var" in md


def test_052_format_deterministik_sira() -> None:
    """Aynı raporun iki markdown çağrısında bölüm sırası aynı."""
    from atlas_core.memory.vault_verify import BrokenLink
    rep = VerifyReport(
        broken_links=[BrokenLink(frm="a", to="x"), BrokenLink(frm="b", to="y")],
        orphan_notes=["yalniz1", "yalniz2"],
        orphan_tags=["tek1", "tek2"],
    )
    md1 = format_report_markdown(rep, "vault")
    md2 = format_report_markdown(rep, "vault")
    # Timestamp haricinde deterministik — timestamp UTC şu anlık
    # test aynı saniyede çalışıyor; drop first 3 lines (title + boş + ts)
    def _strip_ts(m: str) -> str:
        return "\n".join(m.splitlines()[3:])
    assert _strip_ts(md1) == _strip_ts(md2)


def test_052_format_utf8_karakterler() -> None:
    """Türkçe not adları + tag'ler bozulmadan basılır."""
    from atlas_core.memory.vault_verify import BrokenLink
    rep = VerifyReport(
        broken_links=[BrokenLink(frm="günlük", to="özet")],
        orphan_tags=["çığır"],
    )
    md = format_report_markdown(rep, "vault")
    assert "`günlük` → `özet`" in md
    assert "`#çığır`" in md


# ═════════════════════════════════════════════════════════════════════
# CLI: --dump-report
# ═════════════════════════════════════════════════════════════════════


def test_052_cli_dump_report_dosya_yazilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--dump-report PATH` → markdown dosyaya yazılır; stdout etkilenmez."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")
    dump = tmp_path / ".atlas" / "vault-health.md"

    rc = main([
        "vault", "verify",
        "--vault-root", str(v),
        "--dump-report", str(dump),
    ])
    assert rc == 0
    assert dump.is_file()
    md = dump.read_text(encoding="utf-8")
    assert "# ATLAS vault verify raporu" in md
    assert "## Kırık linkler (1)" in md
    # Stdout hâlâ insan formatını basar (bit-uyumlu)
    out = capsys.readouterr().out
    assert "=== ATLAS vault verify" in out


def test_052_cli_dump_report_dizin_yoksa_olusturur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Hedef dizin (`--dump-report a/b/c.md`) yoksa parents oluşturulur."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("solo", encoding="utf-8")
    dump = tmp_path / "yeni" / "iç" / "rapor.md"

    rc = main([
        "vault", "verify",
        "--vault-root", str(v),
        "--dump-report", str(dump),
    ])
    assert rc == 0
    assert dump.is_file()


def test_052_cli_dump_report_ile_strict_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--strict --dump-report` bulgu varsa exit 4 KORUR + dosya yazılır."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")
    dump = tmp_path / "health.md"

    rc = main([
        "vault", "verify",
        "--vault-root", str(v),
        "--strict",
        "--dump-report", str(dump),
    ])
    assert rc == 4  # bit-uyumlu SPEC 042 exit
    assert dump.is_file()
    md = dump.read_text(encoding="utf-8")
    assert "durum: ❌ bulgu var" in md


def test_052_cli_dump_report_yazma_hatasi_sessiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Dump yazımı OSError → verify çıktı sözleşmesi bit-uyumlu (sessiz).

    Hook contextinde commit'i patlatmamak için tasarlandı.
    """
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("solo", encoding="utf-8")
    # Yazılamaz yol: mevcut dosya + parent olarak istenirse OSError
    existing_file = tmp_path / "file.txt"
    existing_file.write_text("engel", encoding="utf-8")
    dump = existing_file / "sub" / "rapor.md"

    rc = main([
        "vault", "verify",
        "--vault-root", str(v),
        "--dump-report", str(dump),
    ])
    assert rc == 0  # verify başarılı; dump sessiz düştü


def test_052_cli_json_ile_dump_report_birlikte(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json --dump-report` ortogonal: JSON stdout + markdown dosya."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")
    dump = tmp_path / "health.md"

    rc = main([
        "vault", "verify",
        "--vault-root", str(v),
        "--json",
        "--dump-report", str(dump),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"broken_links"' in out  # JSON stdout
    assert dump.is_file()
    md = dump.read_text(encoding="utf-8")
    assert "# ATLAS vault verify raporu" in md  # Markdown dosya

"""SPEC 046 — atlas vault fix-orphans (birim + CLI)."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault import Vault
from atlas_core.memory.vault_verify import (
    _find_orphan_paths,
    _unique_dst,
    archive_orphan_notes,
    verify_graph,
)


def _make_vault(root: Path, notes: dict[str, str]) -> Vault:
    """Not adı `folder/name.md` da olabilir."""
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in notes.items():
        if "/" in rel:
            path = root / f"{rel}.md"
        else:
            path = root / f"{rel}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return Vault(root)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


# ═════════════════════════════════════════════════════════════════════
# _unique_dst
# ═════════════════════════════════════════════════════════════════════


def test_046_unique_dst_bos_klasor(tmp_path: Path) -> None:
    p = tmp_path / "note.md"
    assert _unique_dst(p) == p


def test_046_unique_dst_cakisma_suffix(tmp_path: Path) -> None:
    p = tmp_path / "note.md"
    p.write_text("var", encoding="utf-8")
    result = _unique_dst(p)
    assert result == tmp_path / "note-1.md"


def test_046_unique_dst_ikinci_cakisma(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("var", encoding="utf-8")
    (tmp_path / "note-1.md").write_text("var", encoding="utf-8")
    result = _unique_dst(tmp_path / "note.md")
    assert result == tmp_path / "note-2.md"


# ═════════════════════════════════════════════════════════════════════
# _find_orphan_paths
# ═════════════════════════════════════════════════════════════════════


def test_046_find_orphan_paths_dogru_klasoru_bulur(tmp_path: Path) -> None:
    """Orfan not alt-klasörde olsa bile rglob bulur."""
    v = _make_vault(tmp_path / "v", {
        "a": "[[b]]",
        "b": "[[a]]",
        "daily/2026-08-04": "günlük",  # orfan (alt-klasörde)
    })
    rep = verify_graph(v.graph())
    assert "2026-08-04" in rep.orphan_notes  # stem
    paths = _find_orphan_paths(v, rep.orphan_notes)
    assert len(paths) == 1
    assert paths[0].name == "2026-08-04.md"
    assert paths[0].parent.name == "daily"


# ═════════════════════════════════════════════════════════════════════
# archive_orphan_notes (birim)
# ═════════════════════════════════════════════════════════════════════


def test_046_archive_dry_run_dosyalari_dokunmaz(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {"yalniz": "solo"})
    rep = verify_graph(v.graph())
    target = tmp_path / "arc"

    actions = archive_orphan_notes(
        v, rep.orphan_notes, target, dry_run=True,
    )

    assert len(actions) == 1
    assert actions[0].action == "planned"
    assert actions[0].dst.name == "yalniz.md"
    # Kaynak dokunulmadı; hedef klasör bile oluşmadı
    assert (v.root / "yalniz.md").is_file()
    assert not target.exists()


def test_046_archive_apply_gercek_tasima(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {"yalniz": "solo"})
    rep = verify_graph(v.graph())
    target = tmp_path / "arc"

    actions = archive_orphan_notes(
        v, rep.orphan_notes, target, dry_run=False,
    )

    assert actions[0].action == "moved"
    assert not (v.root / "yalniz.md").exists()
    assert (target / "yalniz.md").read_text(encoding="utf-8") == "solo"


def test_046_archive_cakisma_suffix(tmp_path: Path) -> None:
    """Target'ta aynı isimli dosya varsa `-1.md` suffix."""
    v = _make_vault(tmp_path / "v", {"yalniz": "yeni"})
    rep = verify_graph(v.graph())
    target = tmp_path / "arc"
    target.mkdir()
    (target / "yalniz.md").write_text("eski", encoding="utf-8")

    actions = archive_orphan_notes(
        v, rep.orphan_notes, target, dry_run=False,
    )

    assert actions[0].dst.name == "yalniz-1.md"
    assert (target / "yalniz.md").read_text(encoding="utf-8") == "eski"
    assert (target / "yalniz-1.md").read_text(encoding="utf-8") == "yeni"


def test_046_archive_kaynak_yoksa_skipped(tmp_path: Path) -> None:
    """verify sonrası kaynak silinmiş → skipped (nazikçe atla)."""
    v = _make_vault(tmp_path / "v", {"yalniz": "solo"})
    rep = verify_graph(v.graph())
    # Kaynağı manuel sil (yarış durumunu simüle et)
    (v.root / "yalniz.md").unlink()

    actions = archive_orphan_notes(
        v, rep.orphan_notes, tmp_path / "arc", dry_run=False,
    )
    # rglob artık bulamayacak → boş liste
    assert actions == []


def test_046_archive_orfan_yoksa_bos_liste(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {"a": "[[b]]", "b": "[[a]]"})
    rep = verify_graph(v.graph())
    assert rep.orphan_notes == []
    actions = archive_orphan_notes(v, [], tmp_path / "arc", dry_run=False)
    assert actions == []


def test_046_archive_bircok_orfan_ayni_hedefe(tmp_path: Path) -> None:
    """3 orfan → 3 dosya taşınır."""
    v = _make_vault(tmp_path / "v", {
        "linkli": "[[digeri]]",
        "digeri": "[[linkli]]",
        "yalniz1": "s1",
        "yalniz2": "s2",
        "yalniz3": "s3",
    })
    rep = verify_graph(v.graph())
    assert sorted(rep.orphan_notes) == ["yalniz1", "yalniz2", "yalniz3"]
    target = tmp_path / "arc"

    actions = archive_orphan_notes(
        v, rep.orphan_notes, target, dry_run=False,
    )

    assert len(actions) == 3
    assert all(a.action == "moved" for a in actions)
    for name in ("yalniz1", "yalniz2", "yalniz3"):
        assert (target / f"{name}.md").is_file()
        assert not (v.root / f"{name}.md").exists()


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas vault fix-orphans
# ═════════════════════════════════════════════════════════════════════


def test_046_cli_dry_run_orfan_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[b]]", encoding="utf-8")
    (v / "b.md").write_text("[[a]]", encoding="utf-8")

    rc = main(["vault", "fix-orphans", "--vault-root", str(v)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Orfan not yok" in out


def test_046_cli_dry_run_orfan_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "yalniz.md").write_text("solo", encoding="utf-8")

    rc = main(["vault", "fix-orphans", "--vault-root", str(v)])
    assert rc == 0
    # Dosya dokunulmadı
    assert (v / "yalniz.md").is_file()
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "yalniz.md" in out
    assert "Uygulamak için: atlas vault fix-orphans --apply" in out


def test_046_cli_apply_dosyalari_tasir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "yalniz.md").write_text("solo", encoding="utf-8")

    rc = main(["vault", "fix-orphans", "--vault-root", str(v), "--apply"])
    assert rc == 0
    assert not (v / "yalniz.md").exists()
    # Hedef: vault/_archive/orphans-YYYY-MM-DD/yalniz.md
    archives = list((v / "_archive").glob("orphans-*/yalniz.md"))
    assert len(archives) == 1
    assert archives[0].read_text(encoding="utf-8") == "solo"
    # Audit satırı
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "atlas-vault" in audit
    assert "fix-orphans" in audit


def test_046_cli_apply_custom_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "yalniz.md").write_text("solo", encoding="utf-8")
    custom = tmp_path / "custom-arc"

    rc = main([
        "vault", "fix-orphans",
        "--vault-root", str(v),
        "--target", str(custom),
        "--apply",
    ])
    assert rc == 0
    assert (custom / "yalniz.md").is_file()


def test_046_cli_vault_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "fix-orphans",
        "--vault-root", str(tmp_path / "yok"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_046_cli_verify_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas vault verify` DEĞİŞMEDİ — fix-orphans bağımsız alt-komut."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "yalniz.md").write_text("solo", encoding="utf-8")

    rc = main(["vault", "verify", "--vault-root", str(v)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "orfan not:  1" in out
    # verify DOKUNMADI — dosya hâlâ orada
    assert (v / "yalniz.md").is_file()

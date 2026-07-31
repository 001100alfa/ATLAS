"""SPEC 042 — atlas vault verify testleri (birim + CLI)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault import Vault
from atlas_core.memory.vault_verify import (
    BrokenLink,
    verify_graph,
)


def _make_vault(root: Path, notes: dict[str, str]) -> Vault:
    """`<root>/<name>.md` her bir dosya için içerik yaz; Vault döner."""
    root.mkdir(parents=True, exist_ok=True)
    for name, content in notes.items():
        (root / f"{name}.md").write_text(content, encoding="utf-8")
    return Vault(root)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


# ═════════════════════════════════════════════════════════════════════
# verify_graph (birim)
# ═════════════════════════════════════════════════════════════════════


def test_042_verify_temiz_vault(tmp_path: Path) -> None:
    """Kırık link/orfan yok → is_clean=True."""
    v = _make_vault(tmp_path / "v", {
        "a": "linkli [[b]] #ortak",
        "b": "linkli [[a]] #ortak",
    })
    rep = verify_graph(v.graph())

    assert rep.is_clean is True
    assert rep.broken_links == []
    assert rep.orphan_notes == []
    assert rep.orphan_tags == []
    assert rep.notes_total == 2
    assert rep.links_total == 2  # a->b, b->a
    assert rep.tags_total == 2   # ortak x2


def test_042_verify_kirik_link_tespiti(tmp_path: Path) -> None:
    """`[[yok]]` hedefi olmayan → BrokenLink."""
    v = _make_vault(tmp_path / "v", {
        "a": "linkli [[yok]] ve [[b]]",
        "b": "linkli [[a]]",
    })
    rep = verify_graph(v.graph())

    assert rep.broken_links == [BrokenLink(frm="a", to="yok")]
    assert rep.is_clean is False


def test_042_verify_orfan_not_tespiti(tmp_path: Path) -> None:
    """Ne link veren ne link alan not → orphan."""
    v = _make_vault(tmp_path / "v", {
        "a": "linkli [[b]]",
        "b": "linkli [[a]]",
        "yalniz": "hiç link yok, kimse de bana link vermiyor",
    })
    rep = verify_graph(v.graph())

    assert "yalniz" in rep.orphan_notes
    assert "a" not in rep.orphan_notes
    assert "b" not in rep.orphan_notes


def test_042_verify_orfan_tag_tespiti(tmp_path: Path) -> None:
    """Yalnız 1 notta geçen tag → orfan."""
    v = _make_vault(tmp_path / "v", {
        "a": "#ortak #tek-kullanim",
        "b": "#ortak baska icerik",
    })
    rep = verify_graph(v.graph())

    assert "tek-kullanim" in rep.orphan_tags
    assert "ortak" not in rep.orphan_tags


def test_042_verify_broken_link_deterministik_sira(tmp_path: Path) -> None:
    """Çoklu kırık link (frm, to) sözlük sırasında döner."""
    v = _make_vault(tmp_path / "v", {
        "z": "[[m]] [[b]]",
        "a": "[[k]]",
    })
    rep = verify_graph(v.graph())
    order = [(b.frm, b.to) for b in rep.broken_links]
    assert order == sorted(order)


def test_042_verify_to_dict_serilesebilir(tmp_path: Path) -> None:
    """`to_dict` JSON'a yazılabilir; `from` alan adı literal string."""
    v = _make_vault(tmp_path / "v", {"a": "[[yok]]"})
    rep = verify_graph(v.graph())
    d = rep.to_dict()
    encoded = json.dumps(d)
    assert "\"from\": \"a\"" in encoded
    assert "\"to\": \"yok\"" in encoded
    assert d["is_clean"] is False
    assert d["notes_total"] == 1


def test_042_verify_bos_vault(tmp_path: Path) -> None:
    """Boş vault → temiz, sayaçlar 0."""
    v = _make_vault(tmp_path / "v", {})
    rep = verify_graph(v.graph())
    assert rep.is_clean is True
    assert rep.notes_total == 0
    assert rep.links_total == 0


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas vault verify
# ═════════════════════════════════════════════════════════════════════


def test_042_cli_verify_insan_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[b]]", encoding="utf-8")
    (v / "b.md").write_text("[[a]]", encoding="utf-8")

    rc = main(["vault", "verify", "--vault-root", str(v)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "notlar:" in out
    assert "linkler:" in out
    assert "✔ temiz" in out


def test_042_cli_verify_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")

    rc = main(["vault", "verify", "--vault-root", str(v), "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["broken_links"] == [{"from": "a", "to": "yok"}]
    assert data["is_clean"] is False
    assert data["notes_total"] == 1


def test_042_cli_verify_pretty_indent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("solo", encoding="utf-8")

    rc = main([
        "vault", "verify",
        "--vault-root", str(v),
        "--json", "--pretty",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # Pretty=indent=2 → satır sonu + 2 boşluk
    assert "\n  " in out


def test_042_cli_verify_strict_bulgu_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")

    rc = main([
        "vault", "verify", "--vault-root", str(v), "--strict",
    ])
    assert rc == 4
    err = capsys.readouterr().err
    assert "SAĞLIK BAŞARISIZ" in err


def test_042_cli_verify_strict_temiz_exit_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[b]]", encoding="utf-8")
    (v / "b.md").write_text("[[a]]", encoding="utf-8")

    rc = main([
        "vault", "verify", "--vault-root", str(v), "--strict",
    ])
    assert rc == 0


def test_042_cli_verify_vault_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["vault", "verify", "--vault-root", str(tmp_path / "yok")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_042_cli_verify_audit_kaydi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("solo", encoding="utf-8")

    rc = main(["vault", "verify", "--vault-root", str(v)])
    assert rc == 0
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "atlas-vault" in audit
    assert '"verify"' in audit

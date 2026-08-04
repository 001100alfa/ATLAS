"""SPEC 058 — atlas vault fix-broken (birim + CLI)."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault import Vault
from atlas_core.memory.vault_verify import (
    BrokenLink,
    StubAction,
    create_stub_notes,
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
# create_stub_notes (birim)
# ═════════════════════════════════════════════════════════════════════


def test_058_create_stub_dry_run_dokunmaz(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {"a": "[[yok]]"})
    rep = verify_graph(v.graph())
    target = tmp_path / "_stubs"

    actions = create_stub_notes(v, rep.broken_links, target, dry_run=True)

    assert len(actions) == 1
    assert actions[0].action == "planned"
    assert actions[0].target == "yok"
    assert not target.exists()  # dry-run klasör bile oluşturmaz


def test_058_create_stub_apply_yazar(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {"a": "[[yok]]"})
    rep = verify_graph(v.graph())
    target = tmp_path / "_stubs"

    actions = create_stub_notes(v, rep.broken_links, target, dry_run=False)

    assert actions[0].action == "created"
    stub_path = target / "yok.md"
    assert stub_path.is_file()
    content = stub_path.read_text(encoding="utf-8")
    assert "# yok" in content
    assert "#stub" in content
    assert "SPEC 058" in content
    assert "[[a]]" in content  # kaynak referansı


def test_058_ayni_hedefe_birden_fazla_from_tek_stub(tmp_path: Path) -> None:
    """`[[yok]]` iki farklı nottan → 1 stub + 2 kaynak."""
    v = _make_vault(tmp_path / "v", {
        "a": "[[yok]]",
        "b": "[[yok]] baska icerik",
    })
    rep = verify_graph(v.graph())
    assert len(rep.broken_links) == 2  # (a,yok), (b,yok)
    target = tmp_path / "_stubs"

    actions = create_stub_notes(v, rep.broken_links, target, dry_run=False)

    assert len(actions) == 1  # aynı `yok` hedefi → 1 stub
    assert set(actions[0].sources) == {"a", "b"}
    content = (target / "yok.md").read_text(encoding="utf-8")
    assert "[[a]]" in content
    assert "[[b]]" in content


def test_058_deterministik_sira_ve_kaynak_tekilleme(tmp_path: Path) -> None:
    """Hedef adları sorted; her hedefin kaynak listesi sorted + tekil."""
    v = _make_vault(tmp_path / "v", {
        "z": "[[apple]] [[apple]]",  # aynı kaynak iki kez
        "a": "[[apple]]",
        "m": "[[banana]]",
    })
    rep = verify_graph(v.graph())
    target = tmp_path / "_stubs"

    actions = create_stub_notes(v, rep.broken_links, target, dry_run=False)
    # `apple` ve `banana` sorted → apple önce
    targets_order = [a.target for a in actions]
    assert targets_order == sorted(targets_order)

    apple_stub = next(a for a in actions if a.target == "apple")
    assert apple_stub.sources == ("a", "z")  # sorted; z dup silindi


def test_058_hedef_zaten_var_skipped(tmp_path: Path) -> None:
    """Vault içinde `<to>.md` mevcut (yarış durumu) → skipped."""
    v = _make_vault(tmp_path / "v", {
        "a": "[[yok]]",
        "yok": "aslinda var",  # verify sonrası eklenmiş simülasyon
    })
    # Vault.graph() `yok` var → `[[yok]]` kırık değil zaten. Manuel
    # broken_links üretelim:
    broken = [BrokenLink(frm="a", to="yok")]
    target = tmp_path / "_stubs"

    actions = create_stub_notes(v, broken, target, dry_run=False)

    assert actions[0].action == "skipped"
    assert not (target / "yok.md").exists()  # dokunulmadı


def test_058_bos_broken_links_bos_liste(tmp_path: Path) -> None:
    v = _make_vault(tmp_path / "v", {"a": "[[b]]", "b": "[[a]]"})
    target = tmp_path / "_stubs"
    actions = create_stub_notes(v, [], target, dry_run=False)
    assert actions == []
    assert not target.exists()  # klasör bile oluşmadı


def test_058_stub_action_frozen() -> None:
    """`StubAction` frozen dataclass — immutable."""
    a = StubAction(
        target="x", path=Path("/tmp/x.md"),
        sources=("a", "b"), action="created",
    )
    with pytest.raises((AttributeError, TypeError)):
        a.target = "y"  # type: ignore[misc]


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas vault fix-broken
# ═════════════════════════════════════════════════════════════════════


def test_058_cli_kirik_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[b]]", encoding="utf-8")
    (v / "b.md").write_text("[[a]]", encoding="utf-8")

    rc = main(["vault", "fix-broken", "--vault-root", str(v)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Kirik link yok" in out


def test_058_cli_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")

    rc = main(["vault", "fix-broken", "--vault-root", str(v)])
    assert rc == 0
    # Stub yazılmadı
    assert not (v / "_stubs").exists()
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "yok.md" in out
    assert "Uygulamak icin: atlas vault fix-broken --apply" in out


def test_058_cli_apply_stub_yazar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")

    rc = main(["vault", "fix-broken", "--vault-root", str(v), "--apply"])
    assert rc == 0
    stub = v / "_stubs" / "yok.md"
    assert stub.is_file()
    content = stub.read_text(encoding="utf-8")
    assert "#stub" in content
    # Audit
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "atlas-vault" in audit
    assert "fix-broken" in audit


def test_058_cli_apply_custom_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")
    custom = tmp_path / "custom-stubs"

    rc = main([
        "vault", "fix-broken",
        "--vault-root", str(v),
        "--target", str(custom),
        "--apply",
    ])
    assert rc == 0
    assert (custom / "yok.md").is_file()


def test_058_cli_vault_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "fix-broken",
        "--vault-root", str(tmp_path / "yok"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_058_cli_verify_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas vault verify` DEĞİŞMEDİ — fix-broken bağımsız alt-komut."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")

    rc = main(["vault", "verify", "--vault-root", str(v)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "kırık link: 1" in out
    # verify DOKUNMADI
    assert not (v / "_stubs").exists()


def test_058_cli_apply_ikinci_kez_skipped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """İki kez apply çağır — ikincisi mevcut hedefe skipped der (yarış)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    v.mkdir()
    (v / "a.md").write_text("[[yok]]", encoding="utf-8")

    # 1. apply
    rc1 = main(["vault", "fix-broken", "--vault-root", str(v), "--apply"])
    assert rc1 == 0
    capsys.readouterr()  # clear

    # 2. apply — `yok` artık _stubs/'ta var; verify tekrar hesapladığında
    # broken link YOK (çünkü stub yok.md yok isimli notu sağladı).
    # Yani ikinci çağrı "Kirik link yok" der.
    rc2 = main(["vault", "fix-broken", "--vault-root", str(v), "--apply"])
    assert rc2 == 0
    out = capsys.readouterr().out
    assert "Kirik link yok" in out

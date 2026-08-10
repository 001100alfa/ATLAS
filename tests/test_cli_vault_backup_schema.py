"""SPEC 154 — atlas vault backup --schema testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def test_154_schema_kisa_devre_dizin_gerekmez(monkeypatch, tmp_path, capsys):
    """--schema kısa devre; vault dizini gerekmez."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "backup", "--schema",
        "--vault-root", str(tmp_path / "kesinlikle-yok"),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"


def test_154_schema_top_level_alanlari(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["vault", "backup", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [f["name"] for f in data["top_level"]]
    for expected in ("backup_path", "vault_root", "action",
                     "split_parts", "pruned_count", "encrypted"):
        assert expected in names


def test_154_schema_exit_codes(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["vault", "backup", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    for code in ("0", "2", "6"):
        assert code in data["exit_codes"]


def test_154_schema_formats_human(monkeypatch, tmp_path, capsys):
    """SPEC 041 backup şu an yalnız human çıktı — YAGNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["vault", "backup", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    fmt_names = [f["name"] for f in data["formats"]]
    assert fmt_names == ["human"]


def test_154_schema_notes_spec_referanslari(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["vault", "backup", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    notes_text = " ".join(data["notes"])
    for spec in ("041", "041.1", "041.2", "101", "154"):
        assert f"SPEC {spec}" in notes_text


def test_154_schema_pretty_indent(monkeypatch, tmp_path, capsys):
    """--pretty indent=2 JSON."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "backup", "--schema", "--pretty",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert '\n  "schema_version"' in out


def test_154_backup_normal_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--schema YOKSA SPEC 041 dizin yok hatası (bit-uyumlu davranış)."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "backup",
        "--vault-root", str(tmp_path / "kesinlikle-yok"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "vault dizini yok" in err

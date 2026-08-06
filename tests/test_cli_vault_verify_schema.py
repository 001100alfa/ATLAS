"""SPEC 136 — atlas vault verify --schema testleri."""

from __future__ import annotations

import json

from atlas_core.cli import main


def test_136_schema_kisa_devre(monkeypatch, tmp_path, capsys):
    """--schema → vault dizini gerekmez, JSON şema basılır."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    # ATLAS_VAULT env yok → normalde exit 2, --schema kısa devre → 0
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"
    assert "top_level" in data
    assert "exit_codes" in data
    assert "formats" in data


def test_136_schema_top_level_fields(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [f["name"] for f in data["top_level"]]
    for f in ("notes_total", "links_total", "broken_links",
              "orphan_notes", "orphan_tags"):
        assert f in names


def test_136_schema_exit_codes(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    for code in ("0", "2", "4"):
        assert code in data["exit_codes"]


def test_136_schema_formats(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    fmt_names = [f["name"] for f in data["formats"]]
    for fmt in ("human", "json", "json-pretty", "json-lines"):
        assert fmt in fmt_names


def test_136_schema_pretty(monkeypatch, tmp_path, capsys):
    """--pretty → indent'li JSON."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    rc = main([
        "vault", "verify", "--schema", "--pretty", "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("\n") >= 5  # indent = çok satır
    data = json.loads(out)
    assert "schema_version" in data


def test_136_schema_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--schema YOKSA SPEC 042 verify AYNI (vault yok → exit 2)."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    rc = main(["vault", "verify", "--vault-root", str(tmp_path / "yok")])
    assert rc == 2

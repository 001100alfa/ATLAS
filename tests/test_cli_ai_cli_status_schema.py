"""SPEC 146 — atlas ai-cli status --schema testleri."""

from __future__ import annotations

import json

from atlas_core import cli as cli_mod
from atlas_core.cli import main


def test_146_schema_kisa_devre(monkeypatch, tmp_path, capsys):
    """--schema → dizin gerekmez, JSON şema basılır."""
    # _AI_CLI_DIR yok bile → --schema kısa devre
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "status", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"
    assert "top_level" in data
    assert "exit_codes" in data
    assert "formats" in data


def test_146_schema_top_level_8_alan(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "status", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [f["name"] for f in data["top_level"]]
    for f in ("name", "installed_version", "declared_version",
              "up_to_date", "install_dir", "size_bytes",
              "size_human", "bin_path"):
        assert f in names
    assert len(data["top_level"]) == 8


def test_146_schema_exit_codes(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "status", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    for code in ("0", "2", "4"):
        assert code in data["exit_codes"]


def test_146_schema_formats(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "status", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    fmt_names = [f["name"] for f in data["formats"]]
    for fmt in ("human", "json", "json-lines"):
        assert fmt in fmt_names


def test_146_schema_pretty(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "status", "--schema", "--pretty"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("\n") >= 5
    data = json.loads(out)
    assert "schema_version" in data


def test_146_name_yok_ve_schema_yok_exit_2(monkeypatch, tmp_path, capsys):
    """--schema yok + name yok → SPEC HATASI exit 2."""
    # Sahte ai-cli layout kur (package.json var)
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    (ai / "package.json").write_text(
        json.dumps({"name": "atlas-ai-cli", "dependencies": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "status"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "<name>" in err
    assert "--schema" in err


def test_146_schema_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--schema YOK + name verilirse SPEC 037.4 normal davranış."""
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    (ai / "package.json").write_text(
        json.dumps({"name": "atlas-ai-cli",
                    "dependencies": {"foo": "^1.0.0"}}),
        encoding="utf-8",
    )
    node_mod = ai / "node_modules" / "foo"
    node_mod.mkdir(parents=True)
    (node_mod / "package.json").write_text(
        json.dumps({"name": "foo", "version": "1.0.0"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "status", "foo"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "foo" in out
    assert "kurulu" in out

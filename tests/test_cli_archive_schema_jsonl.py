"""SPEC 171 — atlas archive --schema --format json-lines testleri."""

from __future__ import annotations

import gzip
import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def _lines(stdout: str) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def test_171_jsonl_stream_temel(monkeypatch, tmp_path, capsys):
    """NDJSON stream; son satır summary; tipler var."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "json-lines"])
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    assert lines[-1]["type"] == "summary"
    assert lines[-1]["schema_version"] == "1"
    types = {ln["type"] for ln in lines[:-1]}
    assert "top_level" in types
    assert "exit_code" in types
    assert "format" in types
    assert "sub_command" in types


def test_171_jsonl_summary_sayilari(monkeypatch, tmp_path, capsys):
    """summary sayıları stream'deki tip dağılımına eşit."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "json-lines"])
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    summary = lines[-1]
    body = lines[:-1]
    counts: dict[str, int] = {}
    for ln in body:
        counts[ln["type"]] = counts.get(ln["type"], 0) + 1
    assert counts.get("top_level", 0) == summary["top_level_count"]
    assert counts.get("exit_code", 0) == summary["exit_codes_count"]
    assert counts.get("format", 0) == summary["formats_count"]
    assert counts.get("sub_command", 0) == summary["sub_commands_count"]


def test_171_jsonl_sub_command_alanlari(monkeypatch, tmp_path, capsys):
    """SPEC 164 sub_commands NDJSON satırlarında görünür."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "json-lines"])
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    sc_lines = [ln for ln in lines if ln.get("type") == "sub_command"]
    names = {ln["name"] for ln in sc_lines}
    assert names == {"list", "restore", "search", "all"}
    restore = next(ln for ln in sc_lines if ln["name"] == "restore")
    assert restore["exit_codes"] == ["0", "2", "3", "6"]
    assert restore["spec"] == "033"


def test_171_jsonl_out_yazar(monkeypatch, tmp_path, capsys):
    """--out ile PATH'e stream; stdout boş."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "archive-schema.jsonl"
    rc = main([
        "archive", "--schema", "--format", "json-lines",
        "--out", str(out_path),
    ])
    assert rc == 0
    assert capsys.readouterr().out == ""
    assert out_path.is_file()
    lines = _lines(out_path.read_text(encoding="utf-8"))
    assert lines[-1]["type"] == "summary"


def test_171_jsonl_out_gzip_auto_suffix(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "archive-schema.jsonl"
    rc = main([
        "archive", "--schema", "--format", "json-lines",
        "--out", str(out_path), "--gzip",
    ])
    assert rc == 0
    gz_path = out_path.with_suffix(out_path.suffix + ".gz")
    assert gz_path.is_file()
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        text = fh.read()
    assert '"type": "summary"' in text


def test_171_gzip_out_yoksa_hata(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "archive", "--schema", "--format", "json-lines", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--gzip" in err
    assert "--out" in err


def test_171_normal_archive_jsonl_reddet(monkeypatch, tmp_path, capsys):
    """--schema YOK + --format json-lines → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--list", "--format", "json-lines"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "json-lines" in err
    assert "--schema" in err


def test_171_schema_json_default_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOK → SPEC 149 JSON default AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"
    assert "sub_commands" in data  # SPEC 164


def test_171_schema_prometheus_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 151 --format prometheus çıktısı AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_archive_schema_version" in out
    assert "# HELP" in out

"""SPEC 166 — atlas doctor --schema --format json-lines testleri."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _lines(stdout: str) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def test_166_jsonl_stream_temel(monkeypatch, tmp_path, capsys):
    """NDJSON stream — her satır JSON obje, son satır summary."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "json-lines"])
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    assert lines[-1]["type"] == "summary"
    assert lines[-1]["schema_version"] == "1"
    # En az bir top_level + exit_code + quality_field bekle
    types = {ln["type"] for ln in lines[:-1]}
    assert "top_level" in types
    assert "exit_code" in types
    assert "quality_field" in types


def test_166_jsonl_summary_sayilari(monkeypatch, tmp_path, capsys):
    """summary sayıları stream'deki tip başına dağılıma eşit."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "json-lines"])
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    summary = lines[-1]
    body = lines[:-1]
    counts: dict[str, int] = {}
    for ln in body:
        counts[ln["type"]] = counts.get(ln["type"], 0) + 1
    assert counts.get("top_level", 0) == summary["top_level_count"]
    assert counts.get("quality_field", 0) == summary["quality_fields_count"]
    assert counts.get("exit_code", 0) == summary["exit_codes_count"]
    assert counts.get("backend_option", 0) == summary["backend_options_count"]
    # SPEC 142: retry_pricing + storage env'leri "env" tipinde ama
    # group ile ayrılır
    env_by_group: dict[str, int] = {}
    for ln in body:
        if ln.get("type") == "env":
            g = ln.get("group", "")
            env_by_group[g] = env_by_group.get(g, 0) + 1
    assert env_by_group.get("retry_pricing", 0) == summary["retry_pricing_envs_count"]
    assert env_by_group.get("storage", 0) == summary["storage_envs_count"]


def test_166_jsonl_top_level_alanlar(monkeypatch, tmp_path, capsys):
    """top_level satırlarında name/field_type/desc alanları var."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "json-lines"])
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    tl = [ln for ln in lines if ln.get("type") == "top_level"]
    assert len(tl) >= 1
    for ln in tl:
        assert "name" in ln
        assert "field_type" in ln


def test_166_jsonl_out_yazar(monkeypatch, tmp_path, capsys):
    """--out ile PATH'e stream; stdout boş."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "doctor-schema.jsonl"
    rc = main([
        "doctor", "--schema", "--format", "json-lines",
        "--out", str(out_path),
    ])
    assert rc == 0
    assert capsys.readouterr().out == ""
    assert out_path.is_file()
    lines = _lines(out_path.read_text(encoding="utf-8"))
    assert lines[-1]["type"] == "summary"


def test_166_jsonl_out_gzip_auto_suffix(monkeypatch, tmp_path):
    """--gzip auto-suffix .gz + gzip.open ile okunabilir."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "doctor-schema.jsonl"
    rc = main([
        "doctor", "--schema", "--format", "json-lines",
        "--out", str(out_path), "--gzip",
    ])
    assert rc == 0
    gz_path = out_path.with_suffix(out_path.suffix + ".gz")
    assert gz_path.is_file()
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        text = fh.read()
    assert '"type": "summary"' in text


def test_166_gzip_out_yoksa_hata(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "doctor", "--schema", "--format", "json-lines", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--gzip" in err
    assert "--out" in err


def test_166_normal_doctor_jsonl_reddet(monkeypatch, tmp_path, capsys):
    """--schema YOK + --format json-lines → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--format", "json-lines"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "json-lines" in err
    assert "--schema" in err


def test_166_schema_json_default_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOK → SPEC 040 JSON default AYNI (bit-uyumlu)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"
    assert "top_level" in data
    assert "exit_codes" in data


def test_166_schema_prometheus_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 128 --format prometheus çıktısı AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_doctor_schema_version" in out
    # Prometheus (JSON değil)
    assert "# HELP" in out

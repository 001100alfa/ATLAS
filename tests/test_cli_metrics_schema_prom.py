"""SPEC 157 — atlas metrics --schema --format prometheus testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "kesinlikle-yok.jsonl"))


def test_157_schema_prom_4_metric_ailesi(monkeypatch, tmp_path, capsys):
    """4 metric ailesi HELP+TYPE."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in (
        "atlas_metrics_schema_version",
        "atlas_metrics_schema_top_level",
        "atlas_metrics_schema_exit_code",
        "atlas_metrics_schema_format",
    ):
        assert f"# HELP {name}" in out
        assert f"# TYPE {name} gauge" in out


def test_157_schema_prom_version_metric(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'atlas_metrics_schema_version{version="1"} 1' in out


def test_157_schema_prom_top_level_fields(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in ("ts", "in", "out", "cache_c", "cache_r", "cost", "inflight"):
        assert f'name="{name}"' in out


def test_157_schema_prom_exit_codes(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for code in ("0", "2", "4", "8"):
        assert f'code="{code}"' in out


def test_157_schema_prom_formats(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for fmt in ("human", "json", "prometheus"):
        assert f'name="{fmt}"' in out


def test_157_schema_prom_help_type_4_sayisi(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_metrics_schema_") == 4
    assert out.count("# TYPE atlas_metrics_schema_") == 4


def test_157_schema_json_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOK → SPEC 153 JSON AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "top_level" in data
    assert "formats" in data
    assert data["schema_version"] == "1"


def test_157_normal_prom_dokunulmadi(monkeypatch, tmp_path, capsys):
    """--schema YOK + --format prometheus normal SPEC 043 davranışı AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # SPEC 043 metrics prometheus çıktısı; schema info-metric ADI olmamalı
    assert "atlas_metrics_schema_" not in out

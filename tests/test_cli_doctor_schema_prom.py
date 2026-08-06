"""SPEC 128 — atlas doctor --schema --format prometheus testleri."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def test_128_schema_prom_version(monkeypatch, tmp_path, capsys):
    """schema_version metric var + label."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# HELP atlas_doctor_schema_version" in out
    assert "# TYPE atlas_doctor_schema_version gauge" in out
    assert re.search(r'atlas_doctor_schema_version\{version="\d+"\} 1', out)


def test_128_schema_prom_top_level_fields(monkeypatch, tmp_path, capsys):
    """top_level alan info metric."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# HELP atlas_doctor_schema_top_level_field" in out
    # Bilinen top-level alanlar
    for name in ("schema_version", "backend", "warnings", "quality"):
        assert f'name="{name}"' in out


def test_128_schema_prom_quality_fields(monkeypatch, tmp_path, capsys):
    """quality_fields info metric."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# HELP atlas_doctor_schema_quality_field" in out
    for name in ("decisions_drift", "vault_health", "scan_src"):
        assert f'name="{name}"' in out


def test_128_schema_prom_exit_codes(monkeypatch, tmp_path, capsys):
    """exit_code info metric — 3 bilinen kod (0/8/9)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# HELP atlas_doctor_schema_exit_code" in out
    for code in ("0", "8", "9"):
        assert f'code="{code}"' in out


def test_128_schema_prom_help_type_sayilari(monkeypatch, tmp_path, capsys):
    """4 metric ailesi × HELP+TYPE."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_doctor_schema_") == 4
    assert out.count("# TYPE atlas_doctor_schema_") == 4


def test_128_schema_json_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOKSA SPEC 040 JSON AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema"])
    assert rc == 0
    import json
    data = json.loads(capsys.readouterr().out.strip())
    assert "schema_version" in data
    assert "top_level" in data

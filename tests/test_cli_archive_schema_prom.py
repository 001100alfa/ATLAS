"""SPEC 151 — atlas archive --schema --format prometheus testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def test_151_schema_prom_4_metric_ailesi(monkeypatch, tmp_path, capsys):
    """4 metric ailesi HELP+TYPE."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in (
        "atlas_archive_schema_version",
        "atlas_archive_schema_top_level",
        "atlas_archive_schema_exit_code",
        "atlas_archive_schema_format",
    ):
        assert f"# HELP {name}" in out
        assert f"# TYPE {name} gauge" in out


def test_151_schema_prom_version_metric(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'atlas_archive_schema_version{version="1"} 1' in out


def test_151_schema_prom_top_level_fields(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in ("archive", "task_id", "date", "size_bytes",
                 "size_human", "member_count", "mtime"):
        assert f'name="{name}"' in out


def test_151_schema_prom_exit_codes(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for code in ("0", "2", "3", "6"):
        assert f'code="{code}"' in out


def test_151_schema_prom_formats(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for fmt in ("human", "json", "json-lines"):
        assert f'name="{fmt}"' in out


def test_151_schema_prom_help_type_4_sayisi(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_archive_schema_") == 4
    assert out.count("# TYPE atlas_archive_schema_") == 4


def test_151_schema_json_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOK → SPEC 149 JSON AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "top_level" in data
    assert "formats" in data
    assert data["schema_version"] == "1"


def test_151_normal_archive_format_prom_reddet(monkeypatch, tmp_path, capsys):
    """--format prometheus normal archive modda SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--list", "--format", "prometheus"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "prometheus" in err
    assert "--schema" in err

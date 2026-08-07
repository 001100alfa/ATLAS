"""SPEC 142 — atlas doctor --schema metric ailesi genişletme testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def test_142_schema_json_yeni_alanlar(monkeypatch, tmp_path, capsys):
    """JSON çıktıda backend_options + retry_pricing_envs + storage_envs."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "backend_options" in data
    assert "retry_pricing_envs" in data
    assert "storage_envs" in data
    # backend_options en az 3 giriş (stub/anthropic/acp)
    values = [b["value"] for b in data["backend_options"]]
    for v in ("stub", "anthropic", "acp"):
        assert v in values


def test_142_schema_prom_backend_option_metric(monkeypatch, tmp_path, capsys):
    """--format prometheus → backend_option info-metric ailesi."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# HELP atlas_doctor_schema_backend_option" in out
    assert "# TYPE atlas_doctor_schema_backend_option gauge" in out
    for v in ('value="stub"', 'value="anthropic"', 'value="acp"'):
        assert v in out


def test_142_schema_prom_env_metric(monkeypatch, tmp_path, capsys):
    """--format prometheus → env info-metric (group: retry_pricing|storage)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# HELP atlas_doctor_schema_env" in out
    assert "# TYPE atlas_doctor_schema_env gauge" in out
    assert 'group="retry_pricing"' in out
    assert 'group="storage"' in out
    # Bilinen env adları
    for name in ("ATLAS_LLM_RETRIES", "ATLAS_LLM_PRICE_IN",
                 "ATLAS_VAULT", "ATLAS_AUDIT"):
        assert f'name="{name}"' in out


def test_142_schema_prom_help_type_6_ailesi(monkeypatch, tmp_path, capsys):
    """6 metric ailesi HELP+TYPE (SPEC 128 4 + SPEC 142 2 yeni)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_doctor_schema_") == 6
    assert out.count("# TYPE atlas_doctor_schema_") == 6


def test_142_schema_prom_backend_option_deterministik(monkeypatch, tmp_path, capsys):
    """backend_option satırları liste sırasına göre stabil."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    idx_stub = out.index('value="stub"')
    idx_anth = out.index('value="anthropic"')
    idx_acp = out.index('value="acp"')
    assert idx_stub < idx_anth < idx_acp


def test_142_schema_json_bit_uyumlu_mevcut_alanlar(monkeypatch, tmp_path, capsys):
    """Mevcut top_level/quality_fields/exit_codes/notes AYNI kalır."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "top_level" in data
    assert "quality_fields" in data
    assert "exit_codes" in data
    assert "notes" in data
    assert data["schema_version"] == "1"

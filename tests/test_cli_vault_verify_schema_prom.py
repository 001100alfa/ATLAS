"""SPEC 140 — atlas vault verify --schema --format prometheus testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def test_140_schema_prom_4_metric_ailesi(monkeypatch, tmp_path, capsys):
    """4 metric ailesi HELP+TYPE."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for name in (
        "atlas_vault_verify_schema_version",
        "atlas_vault_verify_schema_top_level",
        "atlas_vault_verify_schema_exit_code",
        "atlas_vault_verify_schema_format",
    ):
        assert f"# HELP {name}" in out
        assert f"# TYPE {name} gauge" in out


def test_140_schema_prom_version_metric(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'atlas_vault_verify_schema_version{version="1"} 1' in out


def test_140_schema_prom_top_level_fields(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for name in ("notes_total", "links_total", "broken_links",
                 "orphan_notes", "orphan_tags"):
        assert f'name="{name}"' in out


def test_140_schema_prom_exit_codes(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for code in ("0", "2", "4"):
        assert f'code="{code}"' in out


def test_140_schema_prom_formats(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for fmt in ("human", "json", "json-pretty", "json-lines"):
        assert f'name="{fmt}"' in out


def test_140_schema_prom_help_type_4_sayisi(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_vault_verify_schema_") == 4
    assert out.count("# TYPE atlas_vault_verify_schema_") == 4


def test_140_schema_json_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOK → SPEC 136 JSON AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "top_level" in data
    assert "formats" in data


def test_140_schema_prom_vault_dizini_gerekmez(monkeypatch, tmp_path, capsys):
    """Vault dizini olmasa da kısa devre çalışır (SPEC 136 AYNI)."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", str(tmp_path / "kesinlikle-yok"),
    ])
    assert rc == 0

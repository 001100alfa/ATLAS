"""SPEC 134 — atlas doctor --schema --format prometheus --out --gzip."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def test_134_schema_prom_out_yazma(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    out = tmp_path / "s.prom"
    rc = main([
        "doctor", "--schema", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert "atlas_doctor_schema_" not in stdout
    assert "atlas_doctor_schema_version" in out.read_text(encoding="utf-8")


def test_134_schema_prom_out_gzip_auto_suffix(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out = tmp_path / "s.prom"
    rc = main([
        "doctor", "--schema", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert not out.is_file()
    assert (tmp_path / "s.prom.gz").is_file()


def test_134_schema_prom_out_decompress_bit_uyumlu(monkeypatch, tmp_path):
    """Gzip decompress → düz metin AYNI."""
    _env(monkeypatch, tmp_path)
    plain = tmp_path / "p.prom"
    rc = main([
        "doctor", "--schema", "--format", "prometheus", "--out", str(plain),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    gz = tmp_path / "g.prom"
    rc = main([
        "doctor", "--schema", "--format", "prometheus",
        "--out", str(gz), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "g.prom.gz", "rt", encoding="utf-8") as fh:
        assert fh.read() == plain_text


def test_134_schema_prom_out_magic_bytes(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out = tmp_path / "s.prom"
    rc = main([
        "doctor", "--schema", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert (tmp_path / "s.prom.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_134_schema_json_out_mutex(monkeypatch, tmp_path, capsys):
    """--schema --out (JSON modu, --format yok) → exit 2."""
    _env(monkeypatch, tmp_path)
    out = tmp_path / "s.json"
    rc = main(["doctor", "--schema", "--out", str(out)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err


def test_134_schema_gzip_out_yok_mutex(monkeypatch, tmp_path, capsys):
    """--schema --gzip (--out yok) → exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus", "--gzip"])
    assert rc == 2


def test_134_schema_prom_out_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--out YOKSA SPEC 128 stdout AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_doctor_schema_version" in out

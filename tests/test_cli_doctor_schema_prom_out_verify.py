"""SPEC 159 — doctor --schema --format prometheus --out --gzip ek kanıt.

SPEC 134 zaten uygulandı; SPEC 155/156 kalıbındaki edge kanıt testleri
doctor için de eklendi (parent auto-mkdir, idempotent .gz suffix,
stdout↔file satır-bazında eşitlik, tam MUTEX mesajı).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def test_159_out_parent_auto_mkdir(monkeypatch, tmp_path):
    """Nested dizin — mkdir(parents=True) kalıbı doğrulaması."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "nested" / "dir" / "doctor-schema.prom"
    rc = main([
        "doctor", "--schema", "--format", "prometheus",
        "--out", str(out_path),
    ])
    assert rc == 0
    assert out_path.is_file()
    assert "atlas_doctor_schema_version" in out_path.read_text(encoding="utf-8")


def test_159_out_gzip_zaten_gz_ise_ikilikatlamaz(monkeypatch, tmp_path):
    """PATH zaten .gz ise ikinci .gz eklenmez (idempotent suffix)."""
    _env(monkeypatch, tmp_path)
    gz_path = tmp_path / "doctor-schema.prom.gz"
    rc = main([
        "doctor", "--schema", "--format", "prometheus",
        "--out", str(gz_path), "--gzip",
    ])
    assert rc == 0
    assert gz_path.is_file()
    double_gz = tmp_path / "doctor-schema.prom.gz.gz"
    assert not double_gz.exists()


def test_159_stdout_file_satir_bazinda_esit(monkeypatch, tmp_path, capsys):
    """--out olmayan mod ile --out düz dosya satır-bazında eşit."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    stdout_text = capsys.readouterr().out.rstrip("\n")
    out_path = tmp_path / "d.prom"
    rc = main([
        "doctor", "--schema", "--format", "prometheus",
        "--out", str(out_path),
    ])
    assert rc == 0
    file_text = out_path.read_text(encoding="utf-8").rstrip("\n")
    assert stdout_text == file_text


def test_159_gzip_out_yok_tam_mutex_mesaji(monkeypatch, tmp_path, capsys):
    """--gzip --out olmadan hem --gzip hem --out err mesajında."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus", "--gzip"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err
    assert "--out" in err

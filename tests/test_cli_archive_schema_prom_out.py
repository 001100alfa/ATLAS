"""SPEC 155 — atlas archive --schema --format prometheus --out --gzip."""

from __future__ import annotations

import gzip

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def test_155_out_yazar_stdout_bos(monkeypatch, tmp_path, capsys):
    """--out ile PATH'e yazar; stdout boş."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "archive-schema.prom"
    rc = main([
        "archive", "--schema", "--format", "prometheus",
        "--out", str(out_path),
    ])
    assert rc == 0
    assert capsys.readouterr().out == ""
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert "atlas_archive_schema_version" in text
    assert 'version="1"' in text


def test_155_out_bit_uyumlu_stdout(monkeypatch, tmp_path, capsys):
    """--out olmayan mod ile --out dosya içeriği aynı satırlar."""
    _env(monkeypatch, tmp_path)
    # stdout modu
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    stdout_text = capsys.readouterr().out.rstrip("\n")
    # file mode
    out_path = tmp_path / "arc.prom"
    rc = main([
        "archive", "--schema", "--format", "prometheus",
        "--out", str(out_path),
    ])
    assert rc == 0
    file_text = out_path.read_text(encoding="utf-8").rstrip("\n")
    assert stdout_text == file_text


def test_155_out_gzip_auto_suffix(monkeypatch, tmp_path):
    """--gzip auto-suffix .gz + gzip.open ile okunabilir."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "archive-schema.prom"
    rc = main([
        "archive", "--schema", "--format", "prometheus",
        "--out", str(out_path), "--gzip",
    ])
    assert rc == 0
    gz_path = out_path.with_suffix(out_path.suffix + ".gz")
    assert gz_path.is_file()
    assert not out_path.is_file()  # sadece .gz uzantılı
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        text = fh.read()
    assert "atlas_archive_schema_version" in text


def test_155_out_gzip_zaten_gz_ise_ikilikatlamaz(monkeypatch, tmp_path):
    """PATH zaten .gz ise ikinci .gz eklenmez."""
    _env(monkeypatch, tmp_path)
    gz_path = tmp_path / "archive-schema.prom.gz"
    rc = main([
        "archive", "--schema", "--format", "prometheus",
        "--out", str(gz_path), "--gzip",
    ])
    assert rc == 0
    assert gz_path.is_file()
    double_gz = tmp_path / "archive-schema.prom.gz.gz"
    assert not double_gz.exists()


def test_155_gzip_out_yoksa_hata(monkeypatch, tmp_path, capsys):
    """--gzip --out olmadan SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "archive", "--schema", "--format", "prometheus", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--gzip" in err
    assert "--out" in err


def test_155_out_parent_auto_mkdir(monkeypatch, tmp_path):
    """Parent dizin yoksa auto-mkdir."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "nested" / "dir" / "schema.prom"
    rc = main([
        "archive", "--schema", "--format", "prometheus",
        "--out", str(out_path),
    ])
    assert rc == 0
    assert out_path.is_file()


def test_155_stdout_bit_uyumlu_out_yoksa(monkeypatch, tmp_path, capsys):
    """--out YOK → SPEC 151 stdout bit-uyumlu."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_archive_schema_version" in out
    assert "# HELP" in out

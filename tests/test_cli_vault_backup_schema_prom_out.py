"""SPEC 163 — atlas vault backup --schema --format prometheus --out --gzip."""

from __future__ import annotations

import gzip

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def _cmd(out=None, gzip_flag=False):
    args = [
        "vault", "backup", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ]
    if out is not None:
        args += ["--out", str(out)]
    if gzip_flag:
        args += ["--gzip"]
    return args


def test_163_out_yazar_stdout_bos(monkeypatch, tmp_path, capsys):
    """--out ile PATH'e yazar; stdout boş."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "vault-backup-schema.prom"
    rc = main(_cmd(out=out_path))
    assert rc == 0
    assert capsys.readouterr().out == ""
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert "atlas_vault_backup_schema_version" in text
    assert 'version="1"' in text


def test_163_out_bit_uyumlu_stdout(monkeypatch, tmp_path, capsys):
    """--out olmayan mod ile --out dosya içeriği aynı satırlar."""
    _env(monkeypatch, tmp_path)
    rc = main(_cmd())
    assert rc == 0
    stdout_text = capsys.readouterr().out.rstrip("\n")
    out_path = tmp_path / "v.prom"
    rc = main(_cmd(out=out_path))
    assert rc == 0
    file_text = out_path.read_text(encoding="utf-8").rstrip("\n")
    assert stdout_text == file_text


def test_163_out_gzip_auto_suffix(monkeypatch, tmp_path):
    """--gzip auto-suffix .gz + gzip.open ile okunabilir."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "vault-backup-schema.prom"
    rc = main(_cmd(out=out_path, gzip_flag=True))
    assert rc == 0
    gz_path = out_path.with_suffix(out_path.suffix + ".gz")
    assert gz_path.is_file()
    assert not out_path.is_file()
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        text = fh.read()
    assert "atlas_vault_backup_schema_version" in text


def test_163_out_gzip_zaten_gz_ise_ikilikatlamaz(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    gz_path = tmp_path / "vault-backup-schema.prom.gz"
    rc = main(_cmd(out=gz_path, gzip_flag=True))
    assert rc == 0
    assert gz_path.is_file()
    double_gz = tmp_path / "vault-backup-schema.prom.gz.gz"
    assert not double_gz.exists()


def test_163_gzip_schema_out_yoksa_hata(monkeypatch, tmp_path, capsys):
    """--schema modda --gzip --out olmadan SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "backup", "--schema", "--format", "prometheus",
        "--vault-root", "yok", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--gzip" in err
    assert "--out" in err


def test_163_out_parent_auto_mkdir(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "nested" / "dir" / "schema.prom"
    rc = main(_cmd(out=out_path))
    assert rc == 0
    assert out_path.is_file()


def test_163_stdout_bit_uyumlu_out_yoksa(monkeypatch, tmp_path, capsys):
    """--out YOK → SPEC 158 stdout bit-uyumlu."""
    _env(monkeypatch, tmp_path)
    rc = main(_cmd())
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_vault_backup_schema_version" in out
    assert "# HELP" in out


def test_163_normal_backup_gzip_reddet(monkeypatch, tmp_path, capsys):
    """--schema YOK + --gzip → normal backup modunda SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "backup", "--gzip",
        "--vault-root", str(tmp_path / "yok"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--gzip" in err
    assert "--schema" in err

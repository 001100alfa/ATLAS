"""SPEC 145 — atlas vault verify --schema --format prometheus --out PATH."""

from __future__ import annotations

import gzip

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.chdir(tmp_path)


def test_145_out_yazma_stdout_bos(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    out = tmp_path / "vs.prom"
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--out", str(out), "--vault-root", "yok",
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert "atlas_vault_verify_schema_" not in stdout
    assert "atlas_vault_verify_schema_version" in out.read_text(encoding="utf-8")


def test_145_out_icerik_stdout_bit_uyumlu(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    # stdout
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    stdout_text = capsys.readouterr().out.strip()
    out = tmp_path / "vs.prom"
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--out", str(out), "--vault-root", "yok",
    ])
    assert rc == 0
    assert out.read_text(encoding="utf-8").strip() == stdout_text


def test_145_out_gzip_auto_suffix(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out = tmp_path / "vs.prom"
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--out", str(out), "--gzip", "--vault-root", "yok",
    ])
    assert rc == 0
    assert not out.is_file()
    gz = tmp_path / "vs.prom.gz"
    assert gz.is_file()
    with gzip.open(gz, "rt", encoding="utf-8") as fh:
        assert "atlas_vault_verify_schema_version" in fh.read()


def test_145_out_parent_auto_mkdir(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out = tmp_path / "deep" / "sub" / "vs.prom"
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--out", str(out), "--vault-root", "yok",
    ])
    assert rc == 0
    assert out.is_file()


def test_145_gzip_out_yok_mutex(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--gzip", "--vault-root", "yok",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err and "--out" in err


def test_145_out_yazma_hatasi(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--out", str(target), "--vault-root", "yok",
    ])
    assert rc == 2


def test_145_out_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    assert "atlas_vault_verify_schema_version" in capsys.readouterr().out

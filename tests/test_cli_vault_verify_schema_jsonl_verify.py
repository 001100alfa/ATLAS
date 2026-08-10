"""SPEC 183 — vault verify --schema --format json-lines --out --gzip ek kanıt.

SPEC 172 zaten uygulandı; SPEC 159 doctor kalıp simetrisindeki 4 edge
kanıt testleri vault verify için de eklendi (parent auto-mkdir,
idempotent .gz suffix, stdout↔file satır-bazında eşitlik, tam MUTEX
mesajı).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def _cmd(*extra):
    return [
        "vault", "verify", "--schema", "--format", "json-lines",
        "--vault-root", "yok",
        *extra,
    ]


def test_183_out_parent_auto_mkdir(monkeypatch, tmp_path):
    """Nested dizin — mkdir(parents=True) kalıbı doğrulaması."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "nested" / "dir" / "vault-verify-schema.jsonl"
    rc = main(_cmd("--out", str(out_path)))
    assert rc == 0
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert '"type": "summary"' in text


def test_183_out_gzip_zaten_gz_ise_ikilikatlamaz(monkeypatch, tmp_path):
    """PATH zaten .gz ise ikinci .gz eklenmez (idempotent suffix)."""
    _env(monkeypatch, tmp_path)
    gz_path = tmp_path / "vault-verify-schema.jsonl.gz"
    rc = main(_cmd("--out", str(gz_path), "--gzip"))
    assert rc == 0
    assert gz_path.is_file()
    double_gz = tmp_path / "vault-verify-schema.jsonl.gz.gz"
    assert not double_gz.exists()


def test_183_stdout_file_satir_bazinda_esit(monkeypatch, tmp_path, capsys):
    """--out olmayan mod ile --out düz dosya satır-bazında eşit."""
    _env(monkeypatch, tmp_path)
    rc = main(_cmd())
    assert rc == 0
    stdout_text = capsys.readouterr().out.rstrip("\n")
    out_path = tmp_path / "vv.jsonl"
    rc = main(_cmd("--out", str(out_path)))
    assert rc == 0
    file_text = out_path.read_text(encoding="utf-8").rstrip("\n")
    assert stdout_text == file_text


def test_183_gzip_out_yok_tam_mutex_mesaji(monkeypatch, tmp_path, capsys):
    """--gzip --out olmadan hem `--gzip` hem `--out` err mesajında."""
    _env(monkeypatch, tmp_path)
    rc = main(_cmd("--gzip"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err
    assert "--out" in err

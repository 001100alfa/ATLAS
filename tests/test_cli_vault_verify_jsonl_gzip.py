"""SPEC 111 — atlas vault verify --format json-lines --out --gzip testleri."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault import Vault


def _make_vault(root: Path, notes: dict[str, str]) -> Vault:
    root.mkdir(parents=True, exist_ok=True)
    for name, content in notes.items():
        (root / f"{name}.md").write_text(content, encoding="utf-8")
    return Vault(root)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def test_111_gzip_auto_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert not out.is_file()
    assert (tmp_path / "r.jsonl.gz").is_file()


def test_111_gzip_decompress_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok1]] [[yok2]]", "orfan": "içerik"})
    # Plain
    plain = tmp_path / "p.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(plain),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    # Gzip
    gz = tmp_path / "g.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(gz), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "g.jsonl.gz", "rt", encoding="utf-8") as fh:
        gz_text = fh.read()
    assert gz_text == plain_text


def test_111_gzip_out_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err
    assert "--out" in err


def test_111_gzip_magic_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert (tmp_path / "r.jsonl.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_111_gzip_strict_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--strict + bulgu + --gzip → exit 4, gzip'e yazılır."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip", "--strict",
    ])
    assert rc == 4
    assert (tmp_path / "r.jsonl.gz").is_file()


def test_111_gzip_ndjson_her_satir_valid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]", "b": "içerik"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "r.jsonl.gz", "rt", encoding="utf-8") as fh:
        for ln in fh.read().strip().split("\n"):
            json.loads(ln)


def test_111_gzip_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out),
    ])
    assert rc == 0
    assert out.read_bytes()[:2] != b"\x1f\x8b"

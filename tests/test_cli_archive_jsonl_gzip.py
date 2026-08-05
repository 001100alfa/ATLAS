"""SPEC 108 — atlas archive --list --json-lines --out --gzip testleri."""

from __future__ import annotations

import gzip
import json
import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _mktar(arc: Path, name: str) -> Path:
    arc.mkdir(parents=True, exist_ok=True)
    p = arc / name
    with tarfile.open(p, "w:gz") as tar:
        info = tarfile.TarInfo(name="x")
        info.size = 0
        tar.addfile(info)
    return p


def test_108_gzip_auto_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert not out.is_file()
    assert (tmp_path / "r.jsonl.gz").is_file()


def test_108_gzip_explicit_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "r.jsonl.gz"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.is_file()
    assert not (tmp_path / "r.jsonl.gz.gz").exists()


def test_108_gzip_decompress_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    _mktar(arc, "b.tar.gz")
    # Plain
    plain = tmp_path / "p.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(plain),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    # Gzip
    gz = tmp_path / "g.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(gz), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    with gzip.open(tmp_path / "g.jsonl.gz", "rt", encoding="utf-8") as fh:
        gz_text = fh.read()
    assert gz_text == plain_text


def test_108_gzip_out_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    rc = main([
        "archive", "--list", "--json-lines", "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err
    assert "--out" in err


def test_108_gzip_magic_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert (tmp_path / "r.jsonl.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_108_gzip_ndjson_her_satir_valid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Gzip decompress edildiğinde her satır valid JSON."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    _mktar(arc, "b.tar.gz")
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    with gzip.open(tmp_path / "r.jsonl.gz", "rt", encoding="utf-8") as fh:
        for ln in fh.read().strip().split("\n"):
            json.loads(ln)


def test_108_gzip_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """--gzip YOK → SPEC 105 düz metin."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.read_bytes()[:2] != b"\x1f\x8b"

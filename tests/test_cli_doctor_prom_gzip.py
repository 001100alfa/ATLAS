"""SPEC 114 — atlas doctor --diff-history-all --format prometheus --out --gzip."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)


def _seed(hist: Path, date: str) -> None:
    hist.mkdir(parents=True, exist_ok=True)
    (hist / f"baseline-{date}.json").write_text(
        json.dumps({"schema_version": 1, "warnings": [], "quality": {}}),
        encoding="utf-8",
    )


def test_114_gzip_auto_suffix(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", "2026-08-05")
    out = tmp_path / "d.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert not out.is_file()
    assert (tmp_path / "d.prom.gz").is_file()


def test_114_gzip_decompress_bit_uyumlu(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", "2026-08-05")
    plain = tmp_path / "p.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(plain),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    gz = tmp_path / "g.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(gz), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "g.prom.gz", "rt", encoding="utf-8") as fh:
        assert fh.read() == plain_text


def test_114_gzip_out_yok_mutex(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", "2026-08-05")
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err and "--out" in err


def test_114_gzip_magic(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", "2026-08-05")
    out = tmp_path / "d.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert (tmp_path / "d.prom.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_114_gzip_gz_uzantı_aynen(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", "2026-08-05")
    out = tmp_path / "d.prom.gz"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert out.is_file()
    assert not (tmp_path / "d.prom.gz.gz").exists()


def test_114_gzip_yoksa_duz(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", "2026-08-05")
    out = tmp_path / "d.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.read_bytes()[:2] != b"\x1f\x8b"

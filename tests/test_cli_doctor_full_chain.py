"""SPEC 123 — doctor --diff-history-all --format prometheus --out --gzip regresyon."""

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


def _seed(hist: Path, dates: list[str]) -> None:
    hist.mkdir(parents=True, exist_ok=True)
    for d in dates:
        (hist / f"baseline-{d}.json").write_text(
            json.dumps({"schema_version": 1, "warnings": [], "quality": {}}),
            encoding="utf-8",
        )


def test_123_tam_zincir_prom_out_gzip(monkeypatch, tmp_path):
    """--diff-history-all + prometheus + out + gzip."""
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history",
          ["2026-08-05", "2026-08-06", "2026-08-07"])
    out = tmp_path / "d.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "d.prom.gz", "rt", encoding="utf-8") as fh:
        text = fh.read()
    # 3 snapshot × 5 metric ailesi
    for d in ("2026-08-05", "2026-08-06", "2026-08-07"):
        assert f'snapshot_date="{d}"' in text
    for name in ("warnings_added", "warnings_removed", "quality_deltas",
                 "has_regression", "has_improvement"):
        assert f"atlas_doctor_history_{name}" in text


def test_123_tam_zincir_strict_ortogonal(monkeypatch, tmp_path):
    """--strict + prom + out + gzip → rc {0,9}, dosya yazılır."""
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", ["2026-08-05"])
    out = tmp_path / "d.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out), "--gzip", "--strict",
    ])
    assert rc in (0, 9)
    assert (tmp_path / "d.prom.gz").is_file()


def test_123_tam_zincir_gzip_yok_duz(monkeypatch, tmp_path):
    """--gzip olmadan düz metin."""
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", ["2026-08-05"])
    out = tmp_path / "d.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "atlas_doctor_history_" in text
    assert out.read_bytes()[:2] != b"\x1f\x8b"


def test_123_tam_zincir_decompress_bit_uyumlu(monkeypatch, tmp_path):
    """Gzip decompress = düz metin AYNI."""
    _env(monkeypatch, tmp_path)
    _seed(tmp_path / ".atlas" / "doctor-history", ["2026-08-05"])
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

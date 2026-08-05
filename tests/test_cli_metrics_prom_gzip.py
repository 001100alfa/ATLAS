"""SPEC 103 — atlas metrics --group-by --format prometheus --out --gzip testleri."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return metrics


def _write_metrics(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


def test_103_gzip_auto_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PATH `.gz` uzantısı yok → otomatik eklenir."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 100}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert not out.is_file()
    gz = tmp_path / "m.prom.gz"
    assert gz.is_file()


def test_103_gzip_explicit_gz_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PATH `.gz` uzantılı → aynen kullanılır (çift .gz.gz olmaz)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 100}])
    out = tmp_path / "m.prom.gz"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert out.is_file()
    assert not (tmp_path / "m.prom.gz.gz").exists()


def test_103_gzip_icerik_decompress_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Gzip decompress → düz metin içerik AYNI."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
    ])
    # 1. Düz
    plain = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(plain),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    # 2. Gzip
    gz = tmp_path / "mg.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(gz), "--gzip",
    ])
    assert rc == 0
    gz_actual = tmp_path / "mg.prom.gz"
    with gzip.open(gz_actual, "rt", encoding="utf-8") as fh:
        gz_text = fh.read()
    assert gz_text == plain_text


def test_103_gzip_out_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--gzip --out yok → SPEC HATASI exit 2."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err
    assert "--out" in err


def test_103_gzip_valid_gzip_magic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dosya gzip magic bytes ile başlar (1f 8b)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    gz = tmp_path / "m.prom.gz"
    magic = gz.read_bytes()[:2]
    assert magic == b"\x1f\x8b"


def test_103_gzip_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--gzip YOK → SPEC 096 düz metin AYNI."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "atlas_metrics_group_records" in text
    # Gzip magic YOK
    assert out.read_bytes()[:2] != b"\x1f\x8b"


def test_103_gzip_auto_suffix_dir_conflict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PATH dizin ismi + auto `.gz` suffix → farklı dosya, başarı 0."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(target), "--gzip",
    ])
    # Auto-suffix nedeniyle as_dir.gz yeni dosya, başarı olur
    assert rc == 0
    assert (tmp_path / "as_dir.gz").is_file()

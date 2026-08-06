"""SPEC 122 — metrics --group-by --format prometheus + --limit regresyon."""

from __future__ import annotations

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


def _write(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


def test_122_limit_prom_son_n(monkeypatch, tmp_path, capsys):
    """--limit N grup Prometheus'a ÖNCE uygulanır (son N kayıt)."""
    metrics = _env(monkeypatch, tmp_path)
    _write(metrics, [
        {"ts": "2026-08-01T10:00:00", "in": 100},  # ilk (limit dışı)
        {"ts": "2026-08-02T10:00:00", "in": 200},  # ilk (limit dışı)
        {"ts": "2026-08-03T10:00:00", "in": 300},  # dahil
        {"ts": "2026-08-04T10:00:00", "in": 400},  # dahil
    ])
    rc = main([
        "metrics", "--group-by", "day", "--format", "prometheus",
        "--limit", "2",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # Sadece son 2 gün gruplandı: 2026-08-03, 2026-08-04
    assert 'key="2026-08-03"' in out
    assert 'key="2026-08-04"' in out
    # İlk 2 gün YOK
    assert 'key="2026-08-01"' not in out
    assert 'key="2026-08-02"' not in out


def test_122_limit_prom_tokens_toplam(monkeypatch, tmp_path, capsys):
    """--limit son 2 kayıt: tokens_in = 300 + 400 = 700."""
    metrics = _env(monkeypatch, tmp_path)
    _write(metrics, [
        {"ts": "2026-08-01T10:00:00", "in": 100},
        {"ts": "2026-08-01T11:00:00", "in": 200},
        {"ts": "2026-08-01T12:00:00", "in": 300},
        {"ts": "2026-08-01T13:00:00", "in": 400},
    ])
    rc = main([
        "metrics", "--group-by", "day", "--format", "prometheus",
        "--limit", "2",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'atlas_metrics_group_tokens_in{unit="day",key="2026-08-01"} 700' in out


def test_122_limit_prom_out_gzip_zincir(monkeypatch, tmp_path):
    """--limit + --format prometheus + --out + --gzip tam zincir."""
    metrics = _env(monkeypatch, tmp_path)
    _write(metrics, [
        {"ts": "2026-08-01T10:00:00", "in": 100},
        {"ts": "2026-08-02T10:00:00", "in": 200},
        {"ts": "2026-08-03T10:00:00", "in": 300},
    ])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "day", "--format", "prometheus",
        "--limit", "1", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    import gzip
    with gzip.open(tmp_path / "m.prom.gz", "rt", encoding="utf-8") as fh:
        text = fh.read()
    # Yalnız son gün
    assert 'key="2026-08-03"' in text
    assert 'key="2026-08-02"' not in text


def test_122_limit_prom_bit_uyumlu_no_limit_default(monkeypatch, tmp_path, capsys):
    """--limit VERİLMEZSE default 20 → 4 kayıt tümü dahil."""
    metrics = _env(monkeypatch, tmp_path)
    _write(metrics, [
        {"ts": f"2026-08-0{i}T10:00:00", "in": i * 100}
        for i in range(1, 5)
    ])
    rc = main([
        "metrics", "--group-by", "day", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for i in range(1, 5):
        assert f'key="2026-08-0{i}"' in out

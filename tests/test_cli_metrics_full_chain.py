"""SPEC 116 — atlas metrics tam zincir regresyon testleri.

SPEC 084 (--with-cost) + SPEC 090 (--format prometheus grup) + SPEC 096
(--out) + SPEC 103 (--gzip) birlikte kullanıldığında beklenen sonuç.
Kod değişikliği yok; regresyon önleme kanıtı.
"""

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
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    return metrics


def _write(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


def test_116_tam_zincir_group_cost_prom_out_gzip(monkeypatch, tmp_path):
    """SPEC 084+090+096+103 tam zincir: dosya + gzip + cost_usd metric."""
    metrics = _env(monkeypatch, tmp_path)
    _write(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 1_000_000, "out": 500_000},
    ])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "day", "--with-cost",
        "--format", "prometheus", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    gz = tmp_path / "m.prom.gz"
    assert gz.is_file()
    with gzip.open(gz, "rt", encoding="utf-8") as fh:
        text = fh.read()
    # SPEC 090: 5 base metric ailesi + SPEC 084 cost_usd
    for name in (
        "atlas_metrics_group_records",
        "atlas_metrics_group_tokens_in",
        "atlas_metrics_group_tokens_out",
        "atlas_metrics_group_cache_creation",
        "atlas_metrics_group_cache_read",
        "atlas_metrics_group_cost_usd",
    ):
        assert f"# HELP {name}" in text
        assert f"# TYPE {name}" in text
    # SPEC 084: 1M*3 + 500k*15 = 10.5 USD
    assert "10.500000" in text


def test_116_tam_zincir_labels_deterministik(monkeypatch, tmp_path):
    """Multi-day: grup sırası key alfabetik (kronolojik)."""
    metrics = _env(monkeypatch, tmp_path)
    _write(metrics, [
        {"ts": "2026-08-06T14:00:00", "in": 2_000_000},
        {"ts": "2026-08-05T14:00:00", "in": 1_000_000},
    ])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "day", "--with-cost",
        "--format", "prometheus", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "m.prom.gz", "rt", encoding="utf-8") as fh:
        text = fh.read()
    idx_5 = text.index('key="2026-08-05"')
    idx_6 = text.index('key="2026-08-06"')
    assert idx_5 < idx_6


def test_116_tam_zincir_gzip_yok_duz(monkeypatch, tmp_path):
    """--gzip olmadan aynı zincir düz metin dosya."""
    metrics = _env(monkeypatch, tmp_path)
    _write(metrics, [{"ts": "2026-08-05T14:00:00", "in": 100}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "day", "--with-cost",
        "--format", "prometheus", "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    assert out.read_bytes()[:2] != b"\x1f\x8b"
    assert "atlas_metrics_group_cost_usd" in out.read_text(encoding="utf-8")


def test_116_tam_zincir_env_fiyat_yok_cost_0(monkeypatch, tmp_path):
    """Env fiyat YOK → cost_usd 0 (fail-safe, workflow durmaz)."""
    monkeypatch.delenv("ATLAS_LLM_PRICE_IN", raising=False)
    monkeypatch.delenv("ATLAS_LLM_PRICE_OUT", raising=False)
    metrics = _env(monkeypatch, tmp_path)
    monkeypatch.delenv("ATLAS_LLM_PRICE_IN", raising=False)
    monkeypatch.delenv("ATLAS_LLM_PRICE_OUT", raising=False)
    _write(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1_000_000}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "day", "--with-cost",
        "--format", "prometheus", "--out", str(out),
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    # Cost sıfır olarak yayımlanır (0.000000)
    assert "atlas_metrics_group_cost_usd" in text
    assert "0.000000" in text

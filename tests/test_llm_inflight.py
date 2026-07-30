"""SPEC 039 — LLM inflight metriği testleri.

Amaç: `_inflight_begin/end` thread-safe sayaç ve `_write_metric_for_data`
opsiyonel `inflight` alanı doğrula. `_call_anthropic` wrapper
`try/finally` ile sayaç leak etmediğini test et.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from atlas_core.orchestrator import planner as pl


def test_039_begin_end_sayac(monkeypatch: pytest.MonkeyPatch) -> None:
    """Baseline sıfır; begin → +1; end → -1; snapshot mevcut değer."""
    # Test izolasyonu — global sayacı reset
    monkeypatch.setattr(pl, "_INFLIGHT_COUNT", 0)
    assert pl._inflight_snapshot() == 0
    n1 = pl._inflight_begin()
    assert n1 == 1
    n2 = pl._inflight_begin()
    assert n2 == 2
    assert pl._inflight_snapshot() == 2
    pl._inflight_end()
    assert pl._inflight_snapshot() == 1
    pl._inflight_end()
    assert pl._inflight_snapshot() == 0


def test_039_end_negatife_dusmez(monkeypatch: pytest.MonkeyPatch) -> None:
    """end() 0'da kaldıysa negatife düşmez (defensive)."""
    monkeypatch.setattr(pl, "_INFLIGHT_COUNT", 0)
    pl._inflight_end()  # Zaten 0
    assert pl._inflight_snapshot() == 0


def test_039_thread_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    """10 thread × 100 begin/end → sayaç 0'a döner (race yok)."""
    monkeypatch.setattr(pl, "_INFLIGHT_COUNT", 0)

    def worker() -> None:
        for _ in range(100):
            pl._inflight_begin()
            pl._inflight_end()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert pl._inflight_snapshot() == 0


def test_039_metrics_inflight_alani_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`_write_metric_for_data(data, inflight=2)` → JSONL'de `inflight: 2`."""
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))

    usage_data = {"usage": {"input_tokens": 10, "output_tokens": 5}}
    pl._write_metric_for_data(usage_data, inflight=2)

    line = metrics.read_text(encoding="utf-8").strip().splitlines()[-1]
    rec = json.loads(line)
    assert rec["inflight"] == 2
    assert rec["in"] == 10
    assert rec["out"] == 5


def test_039_metrics_inflight_yok_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`inflight=None` (varsayılan) → alan yazılmaz (bit-uyumluluk)."""
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))

    usage_data = {"usage": {"input_tokens": 3, "output_tokens": 1}}
    pl._write_metric_for_data(usage_data)  # inflight geçmedik

    rec = json.loads(metrics.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert "inflight" not in rec  # eski sözleşme korundu
    assert rec["in"] == 3


def test_039_call_anthropic_wrapper_finally_sayac_sifir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_call_anthropic_inner` patlarsa da wrapper end() çağırır → sayaç 0."""
    monkeypatch.setattr(pl, "_INFLIGHT_COUNT", 0)

    def _boom(*_a, **_kw):  # type: ignore[no-untyped-def]
        raise pl.LLMPlannerError("boom (test)")

    monkeypatch.setattr(pl, "_call_anthropic_inner", _boom)
    with pytest.raises(pl.LLMPlannerError, match="boom"):
        pl._call_anthropic("k", "u", "m", "p", 5)
    assert pl._inflight_snapshot() == 0


def test_039_call_anthropic_wrapper_basari_sayac_sifir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Başarılı çağrı sonrası inflight sayacı yine 0 (leak yok)."""
    monkeypatch.setattr(pl, "_INFLIGHT_COUNT", 0)

    def _ok(*_a, inflight_at_start: int = 0, **_kw):  # type: ignore[no-untyped-def]
        # inflight snapshot 1 olmalı (dahil sayarak)
        assert inflight_at_start == 1
        return "plan_line"

    monkeypatch.setattr(pl, "_call_anthropic_inner", _ok)
    result = pl._call_anthropic("k", "u", "m", "p", 5)
    assert result == "plan_line"
    assert pl._inflight_snapshot() == 0

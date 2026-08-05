"""SPEC 084 — atlas metrics --group-by --with-cost testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import _group_cost_usd, main


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


# ═════════════════════════════════════════════════════════════════════
# _group_cost_usd birim
# ═════════════════════════════════════════════════════════════════════


def test_084_group_cost_usd_zero_prices() -> None:
    """Fiyat 0 → cost 0."""
    g = {"tokens_in": 1000, "tokens_out": 500, "cache_creation": 100,
         "cache_read": 200}
    assert _group_cost_usd(g, 0.0, 0.0) == 0.0


def test_084_group_cost_usd_hesap() -> None:
    """Prometheus formülü ile bit-uyumlu (in*Pin + cc*Pin*1.25 + cr*Pin*0.1 + out*Pout)/1M."""
    g = {"tokens_in": 1_000_000, "tokens_out": 500_000,
         "cache_creation": 100_000, "cache_read": 200_000}
    # Pin=$3, Pout=$15
    expected = (
        1_000_000 * 3.0 / 1_000_000
        + 100_000 * 3.0 * 1.25 / 1_000_000
        + 200_000 * 3.0 * 0.1 / 1_000_000
        + 500_000 * 15.0 / 1_000_000
    )
    got = _group_cost_usd(g, 3.0, 15.0)
    assert abs(got - expected) < 1e-9


def test_084_group_cost_usd_bos_alanlar() -> None:
    """Alan yoksa 0 kabul edilir (fail-safe)."""
    assert _group_cost_usd({}, 3.0, 15.0) == 0.0


# ═════════════════════════════════════════════════════════════════════
# CLI --with-cost
# ═════════════════════════════════════════════════════════════════════


def test_084_with_cost_group_by_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--group-by hour --with-cost --json → grup dict'te cost_usd alanı."""
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 1_000_000, "out": 500_000},
    ])
    rc = main(["metrics", "--group-by", "hour", "--with-cost", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data["groups"]) == 1
    g = data["groups"][0]
    assert "cost_usd" in g
    # 1M*3/1M + 500k*15/1M = 3 + 7.5 = 10.5
    assert abs(g["cost_usd"] - 10.5) < 1e-6


def test_084_with_cost_env_yok_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Fiyat env yok → cost 0.0, UYARI stderr'e (pretty)."""
    monkeypatch.delenv("ATLAS_LLM_PRICE_IN", raising=False)
    monkeypatch.delenv("ATLAS_LLM_PRICE_OUT", raising=False)
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
    ])
    rc = main(["metrics", "--group-by", "hour", "--with-cost"])
    assert rc == 0
    cap = capsys.readouterr()
    assert "UYARI" in cap.err
    assert "fiyat env yok" in cap.err
    assert "cost" in cap.out  # sütun başlığı


def test_084_with_cost_pretty_sutun(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pretty tabloda cost sütunu görünür."""
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 1000, "out": 500},
    ])
    rc = main(["metrics", "--group-by", "day", "--with-cost"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "cost" in out
    assert "$" in out  # cost sütununda $ prefix


def test_084_with_cost_gerektirir_group_by(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--with-cost tek başına (group-by yok) → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--with-cost"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--with-cost" in err
    assert "--group-by" in err


def test_084_no_with_cost_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--with-cost YOK → SPEC 081 bit-uyumlu (grup dict'te cost_usd YOK)."""
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
    ])
    rc = main(["metrics", "--group-by", "hour", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    g = data["groups"][0]
    assert "cost_usd" not in g  # SPEC 081 alanları AYNI


def test_084_with_cost_cache_hesabi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """cache_c ve cache_r toplamları da cost'a girer (SPEC 043 uyumlu)."""
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 0, "out": 0,
         "cache_c": 1_000_000, "cache_r": 0},
    ])
    rc = main([
        "metrics", "--group-by", "hour", "--with-cost", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    g = data["groups"][0]
    # 1M cache_c * 3 * 1.25 / 1M = 3.75
    assert abs(g["cost_usd"] - 3.75) < 1e-6


def test_084_with_cost_gruplarin_toplam(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Farklı günlerde ayrı grupların ayrı cost'ları."""
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 1_000_000, "out": 0},
        {"ts": "2026-08-06T14:00:00", "in": 2_000_000, "out": 0},
    ])
    rc = main(["metrics", "--group-by", "day", "--with-cost", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data["groups"]) == 2
    assert abs(data["groups"][0]["cost_usd"] - 3.0) < 1e-6
    assert abs(data["groups"][1]["cost_usd"] - 6.0) < 1e-6

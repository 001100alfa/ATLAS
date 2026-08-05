"""SPEC 090 — atlas metrics --group-by --format prometheus + --with-cost."""

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


def _write_metrics(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


def test_090_prometheus_group_hour_temel_metrikler(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """5 temel grup metric: records/tokens_in/out/cache_creation/cache_read."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50,
         "cache_c": 10, "cache_r": 20},
    ])
    rc = main(["metrics", "--group-by", "hour", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in (
        "atlas_metrics_group_records",
        "atlas_metrics_group_tokens_in",
        "atlas_metrics_group_tokens_out",
        "atlas_metrics_group_cache_creation",
        "atlas_metrics_group_cache_read",
    ):
        assert f"# HELP {name}" in out
        assert f"# TYPE {name} counter" in out


def test_090_prometheus_group_labels_unit_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Labels: unit + key."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100},
        {"ts": "2026-08-06T14:00:00", "in": 200},
    ])
    rc = main(["metrics", "--group-by", "day", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'unit="day"' in out
    assert 'key="2026-08-05"' in out
    assert 'key="2026-08-06"' in out


def test_090_prometheus_group_degerler_dogru(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Değerler grupla toplam eşleşmeli."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
        {"ts": "2026-08-05T14:30:00", "in": 200, "out": 100},
    ])
    rc = main(["metrics", "--group-by", "hour", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # tokens_in = 300, tokens_out = 150
    assert 'atlas_metrics_group_tokens_in{unit="hour",key="2026-08-05T14"} 300' in out
    assert 'atlas_metrics_group_tokens_out{unit="hour",key="2026-08-05T14"} 150' in out
    assert 'atlas_metrics_group_records{unit="hour",key="2026-08-05T14"} 2' in out


def test_090_prometheus_group_with_cost_alanlar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--with-cost → cost_usd metric eklenir."""
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 1_000_000, "out": 500_000},
    ])
    rc = main([
        "metrics", "--group-by", "hour", "--with-cost", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_group_cost_usd" in out
    # 3 + 7.5 = 10.5
    assert '10.500000' in out


def test_090_prometheus_group_without_cost_no_cost_metric(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--with-cost yok → cost_usd metric YOK."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100},
    ])
    rc = main(["metrics", "--group-by", "hour", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_group_cost_usd" not in out


def test_090_prometheus_group_alert_mutex_korunur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SPEC 081: --group-by + --alert MUTEX hala geçerli."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    rc = main(["metrics", "--group-by", "hour", "--alert", "50"])
    assert rc == 2


def test_090_prometheus_yalın_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--group-by YOK + --format prometheus → SPEC 043 tekil metrikler AYNI."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
    ])
    rc = main(["metrics", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # SPEC 043 metrikleri
    assert "atlas_metrics_records_total" in out
    assert "atlas_metrics_tokens_prompt_total" in out
    # SPEC 090 grup metrikleri YOK (group_by verilmedi)
    assert "atlas_metrics_group_records" not in out


def test_090_prometheus_group_multiple_days_deterministik(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Grup sırası deterministik (key alfabetik lex = kronolojik)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-06T14:00:00", "in": 200},
        {"ts": "2026-08-05T14:00:00", "in": 100},
        {"ts": "2026-08-07T14:00:00", "in": 300},
    ])
    rc = main(["metrics", "--group-by", "day", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    idx_5 = out.index('key="2026-08-05"')
    idx_6 = out.index('key="2026-08-06"')
    idx_7 = out.index('key="2026-08-07"')
    assert idx_5 < idx_6 < idx_7


def test_090_prometheus_group_help_type_yorumlari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Her metric için HELP+TYPE Prometheus text v0.0.4 uyumlu."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    rc = main(["metrics", "--group-by", "hour", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # 5 base metric × 2 comment satır (HELP + TYPE) minimum 10 satır
    help_count = out.count("# HELP atlas_metrics_group_")
    type_count = out.count("# TYPE atlas_metrics_group_")
    assert help_count == 5
    assert type_count == 5

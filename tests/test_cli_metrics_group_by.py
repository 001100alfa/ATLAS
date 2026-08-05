"""SPEC 081 — atlas metrics --group-by hour|day aggregation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from atlas_core.cli import _group_records_by, main


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
# _group_records_by (birim)
# ═════════════════════════════════════════════════════════════════════


def test_081_group_by_gecersiz_unit() -> None:
    with pytest.raises(ValueError, match="hour"):
        _group_records_by([], "week")


def test_081_group_by_hour_toplam() -> None:
    recs = [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
        {"ts": "2026-08-05T14:30:00", "in": 200, "out": 100},
        {"ts": "2026-08-05T15:00:00", "in": 300, "out": 150},
    ]
    groups = _group_records_by(recs, "hour")
    assert len(groups) == 2
    hour_14 = next(g for g in groups if g["key"] == "2026-08-05T14")
    assert hour_14["records"] == 2
    assert hour_14["tokens_in"] == 300
    assert hour_14["tokens_out"] == 150


def test_081_group_by_day_toplam() -> None:
    recs = [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50, "cache_r": 20},
        {"ts": "2026-08-05T15:00:00", "in": 200, "out": 100, "cache_r": 30},
        {"ts": "2026-08-06T10:00:00", "in": 500, "out": 250, "cache_r": 0},
    ]
    groups = _group_records_by(recs, "day")
    assert len(groups) == 2
    day1 = next(g for g in groups if g["key"] == "2026-08-05")
    assert day1["records"] == 2
    assert day1["tokens_in"] == 300
    assert day1["cache_read"] == 50


def test_081_group_by_ts_bozuk_unknown() -> None:
    """`ts` yok/parse edilemez → 'unknown' grup."""
    recs = [
        {"in": 100},  # ts yok
        {"ts": "not-iso", "in": 200},
        {"ts": "2026-08-05T10:00:00", "in": 50},
    ]
    groups = _group_records_by(recs, "hour")
    keys = [g["key"] for g in groups]
    # unknown sona düşer
    assert keys[-1] == "unknown"
    unknown = next(g for g in groups if g["key"] == "unknown")
    assert unknown["records"] == 2  # ts yok + bozuk


def test_081_group_by_deterministik_sira() -> None:
    recs = [
        {"ts": "2026-08-05T15:00:00", "in": 1},
        {"ts": "2026-08-05T14:00:00", "in": 1},
        {"ts": "2026-08-05T16:00:00", "in": 1},
    ]
    groups = _group_records_by(recs, "hour")
    keys = [g["key"] for g in groups]
    assert keys == ["2026-08-05T14", "2026-08-05T15", "2026-08-05T16"]


# ═════════════════════════════════════════════════════════════════════
# CLI --group-by
# ═════════════════════════════════════════════════════════════════════


def test_081_cli_group_by_hour_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
        {"ts": "2026-08-05T14:30:00", "in": 200, "out": 100},
    ])
    rc = main(["metrics", "--group-by", "hour", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["unit"] == "hour"
    assert len(data["groups"]) == 1
    assert data["groups"][0]["records"] == 2
    assert data["groups"][0]["tokens_in"] == 300


def test_081_cli_group_by_day_insan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
        {"ts": "2026-08-06T10:00:00", "in": 200, "out": 100},
    ])
    rc = main(["metrics", "--group-by", "day"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "--group-by day" in out
    assert "2026-08-05" in out
    assert "2026-08-06" in out


def test_081_cli_group_by_gecersiz_argparse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """--group-by week → argparse choices reddi."""
    _env(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["metrics", "--group-by", "week"])
    assert excinfo.value.code == 2


def test_081_090_cli_group_by_prometheus_no_longer_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SPEC 090: --group-by + --format prometheus MUTEX kaldırıldı,
    artık grup histogram olarak yayımlanır (labels unit, key)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    rc = main(["metrics", "--group-by", "hour", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_group_records" in out
    assert 'unit="hour"' in out
    assert 'key="2026-08-05T14"' in out


def test_081_cli_group_by_alert_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    rc = main(["metrics", "--group-by", "hour", "--alert", "50"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--group-by" in err
    assert "--alert" in err


def test_081_cli_group_by_window_ile_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--window + --group-by birlikte: önce window filtre, sonra group."""
    now = datetime.now()
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        # Window dışı (10 dk önce)
        {"ts": (now - timedelta(minutes=10)).isoformat(timespec="seconds"),
         "in": 999},
        # Window içi (2 dk önce)
        {"ts": (now - timedelta(minutes=2)).isoformat(timespec="seconds"),
         "in": 100},
    ])
    rc = main(["metrics", "--window", "5", "--group-by", "hour", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    # Sadece 1 kayıt window içi
    total_records = sum(g["records"] for g in data["groups"])
    assert total_records == 1


def test_081_cli_group_by_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--group-by yoksa mevcut SPEC 023 insan/JSON çıktı bit-uyumlu."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 1 çağrı" in out
    assert "--group-by" not in out

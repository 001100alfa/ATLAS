"""SPEC 143 — atlas metrics --alert-history-show --format prometheus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _seed(path: Path, recs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r) for r in recs) + "\n",
        encoding="utf-8",
    )


def test_143_prom_help_type_3_metric(monkeypatch, tmp_path, capsys):
    """3 metric ailesi HELP+TYPE."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": ["webhook"]},
    ])
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for name in (
        "atlas_metrics_alert_history_total",
        "atlas_metrics_alert_history_recent",
        "atlas_metrics_alert_channel_total",
    ):
        assert f"# HELP {name}" in out
        assert f"# TYPE {name} counter" in out


def test_143_prom_total_ve_recent_dogru(monkeypatch, tmp_path, capsys):
    """5 kayıt, limit 3 → total=5, recent=3."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": f"2026-08-06T{i:02d}:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []}
        for i in range(1, 6)
    ])
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
        "--limit", "3",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_alert_history_total 5" in out
    assert "atlas_metrics_alert_history_recent 3" in out


def test_143_prom_channel_sayimi(monkeypatch, tmp_path, capsys):
    """channel counter: webhook=2, slack=1, -=1 (boş)."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T10:00:00", "channels": ["webhook"]},
        {"ts": "2026-08-06T11:00:00", "channels": ["webhook", "slack"]},
        {"ts": "2026-08-06T12:00:00", "channels": []},
    ])
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'atlas_metrics_alert_channel_total{channel="webhook"} 2' in out
    assert 'atlas_metrics_alert_channel_total{channel="slack"} 1' in out
    assert 'atlas_metrics_alert_channel_total{channel="-"} 1' in out


def test_143_prom_bos_log(monkeypatch, tmp_path, capsys):
    """Log yok → total=0, recent=0, channel yok."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_alert_history_total 0" in out
    assert "atlas_metrics_alert_history_recent 0" in out


def test_143_prom_deterministik_channel_sirasi(monkeypatch, tmp_path, capsys):
    """Kanal sırası alfabetik lex."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T10:00:00", "channels": ["webhook"]},
        {"ts": "2026-08-06T11:00:00", "channels": ["slack"]},
        {"ts": "2026-08-06T12:00:00", "channels": ["email"]},
    ])
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    idx_e = out.index('channel="email"')
    idx_s = out.index('channel="slack"')
    idx_w = out.index('channel="webhook"')
    assert idx_e < idx_s < idx_w


def test_143_prom_json_mutex(monkeypatch, tmp_path, capsys):
    """--format + --json argparse mutex → SystemExit(2)."""
    _env(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as ei:
        main([
            "metrics", "--alert-history-show", "--format", "prometheus",
            "--json",
        ])
    assert ei.value.code == 2


def test_143_prom_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOK → SPEC 132 pretty tablo AYNI."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main(["metrics", "--alert-history-show"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1/1 kayit" in out
    assert "atlas_metrics_alert_" not in out

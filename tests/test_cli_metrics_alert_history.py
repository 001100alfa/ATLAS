"""SPEC 126 — atlas metrics --alert-history NDJSON log testleri."""

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
    monkeypatch.chdir(tmp_path)
    return metrics


def _write_low_hit_ratio(metrics: Path) -> None:
    """cache_r=0, in=100 → hit_ratio=0%."""
    metrics.write_text(
        json.dumps({"ts": "2026-08-05T14:00:00", "in": 100, "out": 50}) + "\n",
        encoding="utf-8",
    )


def _write_high_hit_ratio(metrics: Path) -> None:
    """cache_r büyük → hit_ratio ~%99."""
    metrics.write_text(
        json.dumps({"ts": "2026-08-05T14:00:00", "in": 1, "out": 50, "cache_r": 1000}) + "\n",
        encoding="utf-8",
    )


def test_126_alert_history_tetikleme_yazi(monkeypatch, tmp_path, capsys):
    """Alert tetiklenir + --alert-history default → .atlas/... satır append."""
    metrics = _env(monkeypatch, tmp_path)
    _write_low_hit_ratio(metrics)
    rc = main(["metrics", "--alert", "50", "--alert-history"])
    assert rc == 8
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    assert history.is_file()
    lines = history.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["alert"] == "cache-hit"
    assert rec["threshold_pct"] == 50.0
    assert rec["hit_ratio_pct"] == 0.0
    assert rec["channels"] == []  # kanal bayrağı yok


def test_126_alert_history_custom_path(monkeypatch, tmp_path):
    """--alert-history PATH custom yol."""
    metrics = _env(monkeypatch, tmp_path)
    _write_low_hit_ratio(metrics)
    custom = tmp_path / "custom" / "alerts.jsonl"
    rc = main(["metrics", "--alert", "50", "--alert-history", str(custom)])
    assert rc == 8
    assert custom.is_file()
    rec = json.loads(custom.read_text(encoding="utf-8").strip())
    assert rec["alert"] == "cache-hit"


def test_126_alert_history_tetiklenmezse_log_yok(monkeypatch, tmp_path):
    """hit_ratio >= threshold → alert tetiklenmez → log YOK."""
    metrics = _env(monkeypatch, tmp_path)
    _write_high_hit_ratio(metrics)
    rc = main(["metrics", "--alert", "50", "--alert-history"])
    assert rc == 0
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    assert not history.exists()


def test_126_alert_history_kanal_listesi(monkeypatch, tmp_path):
    """channels: --alert-webhook + --alert-slack verilirse listede."""
    metrics = _env(monkeypatch, tmp_path)
    _write_low_hit_ratio(metrics)
    rc = main([
        "metrics", "--alert", "50", "--alert-history",
        "--alert-webhook", "https://example.com/hook",
        "--alert-slack", "https://hooks.slack.com/x/y",
    ])
    assert rc == 8
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    rec = json.loads(history.read_text(encoding="utf-8").strip())
    assert "webhook" in rec["channels"]
    assert "slack" in rec["channels"]


def test_126_alert_history_ndjson_append(monkeypatch, tmp_path):
    """İki alert tetiklenirse iki satır (append)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_low_hit_ratio(metrics)
    for _ in range(2):
        rc = main(["metrics", "--alert", "50", "--alert-history"])
        assert rc == 8
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    lines = history.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    for ln in lines:
        rec = json.loads(ln)
        assert rec["alert"] == "cache-hit"


def test_126_alert_history_yoksa_bit_uyumlu(monkeypatch, tmp_path):
    """--alert-history YOKSA SPEC 029 exit 8 aynı; log yok."""
    metrics = _env(monkeypatch, tmp_path)
    _write_low_hit_ratio(metrics)
    rc = main(["metrics", "--alert", "50"])
    assert rc == 8
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    assert not history.exists()


def test_126_alert_history_yazma_hatasi_exit_8(monkeypatch, tmp_path, capsys):
    """PATH mevcut dizin → append başarısız → stderr UYARI + exit 8 KORUNUR."""
    metrics = _env(monkeypatch, tmp_path)
    _write_low_hit_ratio(metrics)
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "metrics", "--alert", "50", "--alert-history", str(target),
    ])
    assert rc == 8
    err = capsys.readouterr().err
    assert "[alert-history] append başarısız" in err

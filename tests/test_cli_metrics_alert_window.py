"""SPEC 169 — atlas metrics --alert-window MINUTES testleri."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)
    return metrics


def _write_records(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def _ts(delta_min: float) -> str:
    """Şimdi - delta_min ISO 8601 (saniye)."""
    return (
        datetime.now() - timedelta(minutes=delta_min)
    ).isoformat(timespec="seconds")


def test_169_alert_window_ayri_pencere_dusuk_hit(monkeypatch, tmp_path, capsys):
    """Eski kayıt (window dışı) yüksek hit, yeni kayıt (window içi) düşük →
    --alert-window verildiğinde ALERT tetiklenir (yeni pencere düşük)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_records(metrics, [
        # 3 saat önce yüksek cache-hit kayıt (eski)
        {"ts": _ts(180), "in": 10, "out": 5, "cache_c": 0, "cache_r": 990,
         "cost": 0.01},
        # 30 dakika önce düşük cache-hit kayıt (yeni)
        {"ts": _ts(30), "in": 100, "out": 5, "cache_c": 0, "cache_r": 5,
         "cost": 0.01},
    ])
    # --alert-window 60 → yalnız son 60 dakika → hit_ratio %5/(100+0+5) ≈ 4.76%
    # Eşik %30, düşük → UYARI + exit 8
    rc = main([
        "metrics", "--limit", "100", "--alert", "30",
        "--alert-window", "60",
    ])
    assert rc == 8
    err = capsys.readouterr().err
    assert "UYARI" in err
    assert "cache-hit" in err


def test_169_alert_window_yeni_yuksek_hit_alarm_yok(monkeypatch, tmp_path, capsys):
    """Yeni kayıt yüksek cache-hit → --alert-window ile alarm yok."""
    metrics = _env(monkeypatch, tmp_path)
    _write_records(metrics, [
        # 3 saat önce düşük cache-hit (eski, window dışı)
        {"ts": _ts(180), "in": 100, "out": 5, "cache_c": 0, "cache_r": 5,
         "cost": 0.01},
        # 30 dakika önce yüksek cache-hit (yeni, window içi)
        {"ts": _ts(30), "in": 10, "out": 5, "cache_c": 0, "cache_r": 990,
         "cost": 0.01},
    ])
    rc = main([
        "metrics", "--limit", "100", "--alert", "30",
        "--alert-window", "60",
    ])
    assert rc == 0  # yeni kayıt yüksek hit → alarm yok


def test_169_alert_window_yoksa_tail_uzerinden(monkeypatch, tmp_path, capsys):
    """--alert-window YOKSA mevcut davranış AYNI (tail üzerinden)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_records(metrics, [
        {"ts": _ts(180), "in": 10, "out": 5, "cache_c": 0, "cache_r": 990,
         "cost": 0.01},
        {"ts": _ts(30), "in": 100, "out": 5, "cache_c": 0, "cache_r": 5,
         "cost": 0.01},
    ])
    # --alert-window YOK → tail (tümü) → hit ratio ortalama %89.5 (yüksek)
    # → alarm yok
    rc = main(["metrics", "--limit", "100", "--alert", "30"])
    assert rc == 0


def test_169_alert_window_gecersiz_deger(monkeypatch, tmp_path, capsys):
    """--alert-window <= 0 → SPEC HATASI exit 2."""
    metrics = _env(monkeypatch, tmp_path)
    _write_records(metrics, [
        {"ts": _ts(1), "in": 100, "out": 5, "cache_c": 0, "cache_r": 5,
         "cost": 0.01},
    ])
    rc = main([
        "metrics", "--limit", "100", "--alert", "30",
        "--alert-window", "0",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--alert-window" in err


def test_169_history_payload_yeni_alanlar(monkeypatch, tmp_path, capsys):
    """SPEC 126 alert-history NDJSON kaydına yeni alanlar
    (`alert_window_minutes`, `alert_window_records`) eklenir."""
    metrics = _env(monkeypatch, tmp_path)
    _write_records(metrics, [
        {"ts": _ts(30), "in": 100, "out": 5, "cache_c": 0, "cache_r": 5,
         "cost": 0.01},
    ])
    history = tmp_path / "alert-history.jsonl"
    rc = main([
        "metrics", "--limit", "100", "--alert", "30",
        "--alert-window", "60",
        "--alert-history", str(history),
    ])
    assert rc == 8
    assert history.is_file()
    lines = [
        json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 1
    rec = lines[0]
    assert rec["alert"] == "cache-hit"
    assert rec["alert_window_minutes"] == 60
    assert rec["alert_window_records"] >= 1


def test_169_history_payload_alan_yok_window_yoksa(monkeypatch, tmp_path, capsys):
    """--alert-window YOKSA `alert_window_*` alanları yazılmaz (bit-uyumlu)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_records(metrics, [
        {"ts": _ts(30), "in": 100, "out": 5, "cache_c": 0, "cache_r": 5,
         "cost": 0.01},
    ])
    history = tmp_path / "alert-history.jsonl"
    rc = main([
        "metrics", "--limit", "100", "--alert", "30",
        "--alert-history", str(history),
    ])
    assert rc == 8
    lines = [
        json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rec = lines[0]
    assert "alert_window_minutes" not in rec
    assert "alert_window_records" not in rec


def test_169_alert_window_alert_yoksa_etkisiz(monkeypatch, tmp_path, capsys):
    """--alert-window --alert olmadan verilirse etkisiz (SPEC 029 alarmı
    zaten kapalı — bit-uyumluluk)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_records(metrics, [
        {"ts": _ts(30), "in": 100, "out": 5, "cache_c": 0, "cache_r": 5,
         "cost": 0.01},
    ])
    rc = main([
        "metrics", "--limit", "100",
        "--alert-window", "60",
    ])
    assert rc == 0
    # rapor normal basılır (alarm yok)

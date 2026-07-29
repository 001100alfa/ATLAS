"""SPEC 023 — cache-hit metrics testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.orchestrator import planner as planner_mod


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return metrics


def _write_metrics_file(path: Path, records: list[dict]) -> None:
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_023_write_metric_dosya_yaratir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`_write_metric_for_data` dosya yoksa oluşturur."""
    metrics = _env(monkeypatch, tmp_path)
    data = {
        "usage": {
            "input_tokens": 100, "output_tokens": 50,
            "cache_creation_input_tokens": 20,
            "cache_read_input_tokens": 30,
        }
    }
    planner_mod._write_metric_for_data(data)
    assert metrics.is_file()
    obj = json.loads(metrics.read_text(encoding="utf-8").strip())
    assert obj["in"] == 100
    assert obj["out"] == 50
    assert obj["cache_c"] == 20
    assert obj["cache_r"] == 30
    assert "ts" in obj


def test_023_write_metric_append_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """İki kayıt append edilir — iki JSON satırı."""
    metrics = _env(monkeypatch, tmp_path)
    data1 = {"usage": {"input_tokens": 10, "output_tokens": 5}}
    data2 = {"usage": {"input_tokens": 20, "output_tokens": 10}}
    planner_mod._write_metric_for_data(data1)
    planner_mod._write_metric_for_data(data2)
    lines = metrics.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["in"] == 10
    assert json.loads(lines[1])["in"] == 20


def test_023_cmd_metrics_insan_format(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas metrics` insan formatı — toplam ve oran görünür."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "?"},
        {"ts": "t2", "in": 200, "out": 100,
         "cache_c": 0, "cache_r": 500, "cost": "?"},
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 2 çağrı" in out
    assert "input tokens:   300" in out
    assert "output tokens:  150" in out
    assert "cache read:     500" in out
    # cache-hit: 500 / (300 + 0 + 500) = 62.5%
    assert "62.5%" in out


def test_023_cmd_metrics_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas metrics --json` JSON liste döner."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "?"},
    ])
    rc = main(["metrics", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["in"] == 100


def test_023_cmd_metrics_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas metrics --limit 2` son 2 kaydı özetler."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 0, "cache_c": 0, "cache_r": 0, "cost": "?"},
        {"ts": "t2", "in": 200, "out": 0, "cache_c": 0, "cache_r": 0, "cost": "?"},
        {"ts": "t3", "in": 300, "out": 0, "cache_c": 0, "cache_r": 0, "cost": "?"},
    ])
    rc = main(["metrics", "--limit", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    # son 2: 200 + 300 = 500
    assert "input tokens:   500" in out


def test_023_metrics_dosya_yok_no_op(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Metrics dosyası yoksa boş özet + exit 0."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 0 çağrı" in out


def test_023_write_metric_disk_hata_sessiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Disk yazma hatası ana akışı bloklamamalı (sessiz no-op)."""
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "readonly" / "m.jsonl"))
    # Klasör oluşturmak isteyecek ama izinden bağımsız hata sessiz kalmalı
    # (yazma yolunda hata çıksa dahi exception yok)
    planner_mod._write_metric_for_data(
        {"usage": {"input_tokens": 1, "output_tokens": 1}}
    )
    # test geçerse hata bloklanmadı

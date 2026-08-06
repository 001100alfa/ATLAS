"""SPEC 132 — atlas metrics --alert-history-show testleri."""

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


def test_132_show_dosya_yok_bos(monkeypatch, tmp_path, capsys):
    """Dosya yok → boş çıktı + rc 0."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--alert-history-show"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "0/0 kayit" in out
    assert "(alert kaydi yok)" in out


def test_132_show_tablo(monkeypatch, tmp_path, capsys):
    """3 kayıt → tablo (default limit 10)."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": ["webhook"]},
        {"ts": "2026-08-05T15:00:00", "hit_ratio_pct": 20.0,
         "threshold_pct": 50.0, "channels": []},
        {"ts": "2026-08-05T16:00:00", "hit_ratio_pct": 30.0,
         "threshold_pct": 50.0, "channels": ["slack"]},
    ])
    rc = main(["metrics", "--alert-history-show"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "3/3 kayit" in out
    assert "2026-08-05T14:00:00" in out
    assert "webhook" in out
    assert "slack" in out


def test_132_show_limit(monkeypatch, tmp_path, capsys):
    """--limit 2 → son 2 kayıt."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": f"2026-08-05T{i:02d}:00:00", "hit_ratio_pct": float(i),
         "threshold_pct": 50.0, "channels": []}
        for i in range(1, 6)
    ])
    rc = main(["metrics", "--alert-history-show", "--limit", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "2/5 kayit" in out
    # Son 2: T04 ve T05
    assert "2026-08-05T04:00:00" in out
    assert "2026-08-05T05:00:00" in out
    # İlk kayıtlar YOK
    assert "2026-08-05T01:00:00" not in out


def test_132_show_json(monkeypatch, tmp_path, capsys):
    """--json → NDJSON stream + summary."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main(["metrics", "--alert-history-show", "--json"])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 2  # 1 record + summary
    rec = json.loads(lines[0])
    summary = json.loads(lines[1])
    assert rec["ts"] == "2026-08-05T14:00:00"
    assert summary["type"] == "summary"
    assert summary["count"] == 1
    assert summary["total"] == 1


def test_132_show_custom_path(monkeypatch, tmp_path, capsys):
    """--alert-history-show PATH custom yol."""
    _env(monkeypatch, tmp_path)
    custom = tmp_path / "custom" / "alerts.jsonl"
    _seed(custom, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main(["metrics", "--alert-history-show", str(custom)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1/1 kayit" in out


def test_132_show_bit_uyumlu_metrics(monkeypatch, tmp_path, capsys):
    """--alert-history-show YOKSA SPEC 023 metrics özet AYNI."""
    _env(monkeypatch, tmp_path)
    (tmp_path / "m.jsonl").write_text(
        json.dumps({"ts": "2026-08-05T14:00:00", "in": 100}) + "\n",
        encoding="utf-8",
    )
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    # SPEC 023 metrics özet başlığı
    assert "ATLAS metrics" in out or "cache-hit" in out or "100" in out

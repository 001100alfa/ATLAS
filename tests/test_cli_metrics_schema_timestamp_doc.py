"""SPEC 195 — metrics --schema alert_payload timestamp belge."""

from __future__ import annotations

import json

from atlas_core.cli import main


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    rc = main(["metrics", "--schema"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_195_timestamp_alani(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in d["alert_payload"]}
    assert "timestamp" in names
    by = {f["name"]: f for f in d["alert_payload"]}
    assert by["timestamp"]["spec"] == "187"
    assert "webhook" in by["timestamp"]["when"]


def test_195_notes_referanslari(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    for s in ("187", "195"):
        assert f"SPEC {s}" in text


def test_195_mevcut_alanlar_korundu(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in d["alert_payload"]}
    # SPEC 175 mevcut 13 + SPEC 195 1 = 14
    assert names == {
        "ts", "alert", "hit_ratio_pct", "threshold_pct", "records",
        "tokens_in", "tokens_out", "cache_creation", "cache_read",
        "message", "channels",
        "alert_window_minutes", "alert_window_records",
        "timestamp",
    }

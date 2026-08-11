"""SPEC 197 — doctor --schema alert_payload timestamp belge."""

from __future__ import annotations

import json

from atlas_core.cli import main


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)
    rc = main(["doctor", "--schema"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_197_timestamp_alani(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in d["alert_payload"]}
    assert "timestamp" in names
    by = {f["name"]: f for f in d["alert_payload"]}
    assert by["timestamp"]["spec"] == "192"


def test_197_alan_sayisi_5(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in d["alert_payload"]}
    assert names == {"alert", "warnings", "quality_warnings",
                     "strict", "timestamp"}


def test_197_notes_referanslari(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    for s in ("192", "197"):
        assert f"SPEC {s}" in text


def test_197_alert_options_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 181 alert_options 1 seçenek AYNI."""
    d = _schema(monkeypatch, tmp_path, capsys)
    names = [o["name"] for o in d["alert_options"]]
    assert "--alert-webhook URL" in names

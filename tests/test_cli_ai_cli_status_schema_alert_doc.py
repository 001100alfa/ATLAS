"""SPEC 194 — ai-cli status --schema alert_options + alert_payload."""

from __future__ import annotations

import json

from atlas_core.cli import main


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["ai-cli", "status", "--schema"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_194_alert_options(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_options" in d
    assert d["alert_options"][0]["name"] == "--alert-webhook URL"
    assert d["alert_options"][0]["spec"] == "170"


def test_194_alert_payload_8_alan(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in d["alert_payload"]}
    assert names == {"alert", "name", "installed_version",
                     "declared_version", "up_to_date", "install_dir",
                     "size_bytes", "timestamp"}


def test_194_spec_180_alanlari(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    by = {f["name"]: f for f in d["alert_payload"]}
    assert by["size_bytes"]["spec"] == "180"
    assert by["timestamp"]["spec"] == "180"


def test_194_notes_referanslari(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    for s in ("170", "180", "194"):
        assert f"SPEC {s}" in text


def test_194_prometheus_dokunulmadi(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["ai-cli", "status", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_ai_cli_status_schema_") == 4
    assert "atlas_ai_cli_status_schema_alert_option" not in out

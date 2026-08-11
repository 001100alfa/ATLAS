"""SPEC 189 — archive --schema alert_options + alert_payload."""

from __future__ import annotations

import json

from atlas_core.cli import main


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["archive", "--schema"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_189_alert_options(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_options" in d
    names = [o["name"] for o in d["alert_options"]]
    assert "--restore --alert-webhook URL" in names
    assert d["alert_options"][0]["spec"] == "176"


def test_189_alert_payload_6_alan(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_payload" in d
    names = {f["name"] for f in d["alert_payload"]}
    assert names == {"alert", "task_id", "search_pattern",
                     "archive_root", "error", "exit_code"}
    for f in d["alert_payload"]:
        assert f["spec"] == "176"


def test_189_notes_referanslari(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    for s in ("176", "189"):
        assert f"SPEC {s}" in text


def test_189_prometheus_dokunulmadi(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_archive_schema_") == 4
    assert "atlas_archive_schema_alert_option" not in out


def test_189_sub_commands_ve_alanlar_korundu(monkeypatch, tmp_path, capsys):
    """SPEC 164 sub_commands + top_level AYNI."""
    d = _schema(monkeypatch, tmp_path, capsys)
    assert "sub_commands" in d
    assert set(d["sub_commands"].keys()) == {"list", "restore", "search", "all"}
    tl = [f["name"] for f in d["top_level"]]
    assert "archive" in tl

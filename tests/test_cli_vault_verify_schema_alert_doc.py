"""SPEC 188 — vault verify --schema alert_options + alert_payload."""

from __future__ import annotations

import json

from atlas_core.cli import main


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_188_alert_options(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_options" in d
    names = [o["name"] for o in d["alert_options"]]
    assert "--alert-webhook URL" in names
    assert d["alert_options"][0]["spec"] == "165"


def test_188_alert_payload_9_alan(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_payload" in d
    names = {f["name"] for f in d["alert_payload"]}
    assert names == {"alert", "vault_root", "notes_total", "links_total",
                     "tags_total", "broken_links", "orphan_notes",
                     "orphan_tags", "timestamp"}


def test_188_timestamp_spec_186(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    by = {f["name"]: f for f in d["alert_payload"]}
    assert by["timestamp"]["spec"] == "186"
    assert by["alert"]["spec"] == "165"


def test_188_notes_referanslari(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    for s in ("165", "186", "188"):
        assert f"SPEC {s}" in text


def test_188_prometheus_dokunulmadi(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["vault", "verify", "--schema", "--format", "prometheus",
               "--vault-root", "yok"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_vault_verify_schema_") == 4
    assert "atlas_vault_verify_schema_alert_option" not in out

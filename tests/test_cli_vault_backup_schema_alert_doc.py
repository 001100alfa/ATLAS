"""SPEC 190 — vault backup --schema alert_options + alert_payload."""

from __future__ import annotations

import json

from atlas_core.cli import main


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["vault", "backup", "--schema", "--vault-root", "yok"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_190_alert_options(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_options" in d
    assert d["alert_options"][0]["name"] == "--alert-webhook URL"
    assert d["alert_options"][0]["spec"] == "178"


def test_190_alert_payload_6_alan(monkeypatch, tmp_path, capsys):
    """SPEC 178 6 + SPEC 199 timestamp = 7."""
    d = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in d["alert_payload"]}
    assert names == {"alert", "vault_root", "action", "phase",
                     "error", "exit_code", "timestamp"}
    by = {f["name"]: f for f in d["alert_payload"]}
    for k in ("alert", "vault_root", "action", "phase", "error", "exit_code"):
        assert by[k]["spec"] == "178"
    assert by["timestamp"]["spec"] == "199"


def test_190_phase_alani(monkeypatch, tmp_path, capsys):
    """phase alanı desc'inde 'backup | prune | split | encrypt' var."""
    d = _schema(monkeypatch, tmp_path, capsys)
    by = {f["name"]: f for f in d["alert_payload"]}
    for w in ("backup", "prune", "split", "encrypt"):
        assert w in by["phase"]["desc"]


def test_190_notes_referanslari(monkeypatch, tmp_path, capsys):
    d = _schema(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    for s in ("178", "190"):
        assert f"SPEC {s}" in text


def test_190_prometheus_dokunulmadi(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["vault", "backup", "--schema", "--format", "prometheus",
               "--vault-root", "yok"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_vault_backup_schema_") == 4
    assert "atlas_vault_backup_schema_alert_option" not in out

"""SPEC 181 — doctor --schema alert_options + alert_payload testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_181_alert_options_alani_var(monkeypatch, tmp_path, capsys):
    """SPEC 181: alert_options alanı 1 CLI seçeneği."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_options" in data
    names = [opt["name"] for opt in data["alert_options"]]
    assert "--alert-webhook URL" in names
    opt = data["alert_options"][0]
    assert opt["spec"] == "168"


def test_181_alert_payload_4_alan(monkeypatch, tmp_path, capsys):
    """SPEC 181: alert_payload alanı 4 alan (SPEC 168 3 + SPEC 177 1)."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_payload" in data
    names = {f["name"] for f in data["alert_payload"]}
    assert names == {"alert", "warnings", "quality_warnings", "strict"}


def test_181_alert_payload_spec_referanslari(monkeypatch, tmp_path, capsys):
    """alert/warnings/quality_warnings -> SPEC 168; strict -> SPEC 177."""
    data = _schema(monkeypatch, tmp_path, capsys)
    by_name = {f["name"]: f for f in data["alert_payload"]}
    assert by_name["alert"]["spec"] == "168"
    assert by_name["warnings"]["spec"] == "168"
    assert by_name["quality_warnings"]["spec"] == "168"
    assert by_name["strict"]["spec"] == "177"


def test_181_alert_payload_when_always(monkeypatch, tmp_path, capsys):
    """4 alan hepsi `when=always` (POST atılırsa hep yazılır)."""
    data = _schema(monkeypatch, tmp_path, capsys)
    for f in data["alert_payload"]:
        assert f["when"] == "always", f"{f['name']}: {f['when']}"


def test_181_notes_spec_referanslari(monkeypatch, tmp_path, capsys):
    """notes'a SPEC 168 + 177 + 181 satırları eklendi."""
    data = _schema(monkeypatch, tmp_path, capsys)
    notes_text = " ".join(data["notes"])
    for spec in ("168", "177", "181"):
        assert f"SPEC {spec}" in notes_text


def test_181_prometheus_alert_alanlari_yok(monkeypatch, tmp_path, capsys):
    """SPEC 175 kalıbı: alert_options/alert_payload Prometheus çıktısına
    EKLENMEDİ. Mevcut 6 metric aile sayısı korunur (SPEC 142)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # SPEC 142 mevcut 6 metric aile:
    assert out.count("# HELP atlas_doctor_schema_") == 6
    # SPEC 181 alanları YOK:
    assert "atlas_doctor_schema_alert_option" not in out
    assert "atlas_doctor_schema_alert_payload" not in out


def test_181_mevcut_alanlar_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """SPEC 040 mevcut top_level/quality_fields/exit_codes DOKUNULMADI."""
    data = _schema(monkeypatch, tmp_path, capsys)
    # top_level 7 alan
    tl_names = [f["name"] for f in data["top_level"]]
    assert "backend" in tl_names
    assert "quality" in tl_names
    # quality_fields (SPEC 032/032.1/032.2/038)
    q_names = [f["name"] for f in data["quality_fields"]]
    assert "decisions_drift" in q_names
    assert "scan_src" in q_names
    # exit_codes 0/8/9
    assert set(data["exit_codes"].keys()) == {"0", "8", "9"}

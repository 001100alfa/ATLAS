"""SPEC 175 — atlas metrics --schema alert_options + alert_payload testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "yok.jsonl"))


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_175_alert_options_alani_var(monkeypatch, tmp_path, capsys):
    """SPEC 175: alert_options alanı 7 CLI seçeneği."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_options" in data
    names = {opt["name"] for opt in data["alert_options"]}
    assert "--alert PCT" in names
    assert "--alert-window MINUTES" in names
    assert "--alert-email" in names
    assert "--alert-webhook URL" in names
    assert "--alert-slack URL" in names
    assert "--alert-history [PATH]" in names
    assert "--alert-history-show [PATH]" in names


def test_175_alert_options_spec_referanslari(monkeypatch, tmp_path, capsys):
    """Her seçenek doğru SPEC numarasına bağlı."""
    data = _schema(monkeypatch, tmp_path, capsys)
    by_name = {opt["name"]: opt for opt in data["alert_options"]}
    assert by_name["--alert PCT"]["spec"] == "029"
    assert by_name["--alert-window MINUTES"]["spec"] == "169"
    assert by_name["--alert-email"]["spec"] == "059"
    assert by_name["--alert-webhook URL"]["spec"] == "064"
    assert by_name["--alert-slack URL"]["spec"] == "068"
    assert by_name["--alert-history [PATH]"]["spec"] == "126"
    assert by_name["--alert-history-show [PATH]"]["spec"] == "132"


def test_175_alert_payload_alani_var(monkeypatch, tmp_path, capsys):
    """SPEC 175: alert_payload alanı — history + webhook alanları."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert "alert_payload" in data
    names = {f["name"] for f in data["alert_payload"]}
    # Mevcut 9 alan
    for expected in ("ts", "alert", "hit_ratio_pct", "threshold_pct",
                     "records", "tokens_in", "tokens_out",
                     "cache_creation", "cache_read"):
        assert expected in names
    # SPEC 169 iki yeni alan
    assert "alert_window_minutes" in names
    assert "alert_window_records" in names


def test_175_alert_payload_when_kosullari(monkeypatch, tmp_path, capsys):
    """--alert-window alanları `when` alanında SPEC 169'a bağlı olduğunu söyler."""
    data = _schema(monkeypatch, tmp_path, capsys)
    by_name = {f["name"]: f for f in data["alert_payload"]}
    assert "--alert-window" in by_name["alert_window_minutes"]["when"]
    assert "--alert-window" in by_name["alert_window_records"]["when"]
    assert by_name["alert_window_minutes"]["spec"] == "169"
    assert by_name["alert_window_records"]["spec"] == "169"


def test_175_alert_payload_channels_history_only(monkeypatch, tmp_path, capsys):
    """`channels` yalnız history NDJSON'da; `message` yalnız webhook'ta."""
    data = _schema(monkeypatch, tmp_path, capsys)
    by_name = {f["name"]: f for f in data["alert_payload"]}
    assert "history only" in by_name["channels"]["when"]
    assert "webhook only" in by_name["message"]["when"]


def test_175_notes_spec_referanslari(monkeypatch, tmp_path, capsys):
    """notes'a SPEC 169 + SPEC 175 satırları eklendi."""
    data = _schema(monkeypatch, tmp_path, capsys)
    notes_text = " ".join(data["notes"])
    assert "SPEC 169" in notes_text
    assert "SPEC 175" in notes_text


def test_175_prometheus_alert_alanlari_yok(monkeypatch, tmp_path, capsys):
    """SPEC 175: alert_options/alert_payload Prometheus çıktısına EKLENMEDİ."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # SPEC 164 kalıbı — mevcut 4 metric aile sayısı korunur
    assert out.count("# HELP atlas_metrics_schema_") == 4
    assert "atlas_metrics_schema_alert_option" not in out
    assert "atlas_metrics_schema_alert_payload" not in out


def test_175_mevcut_alanlar_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """SPEC 153 mevcut top_level/exit_codes/formats DOKUNULMADI."""
    data = _schema(monkeypatch, tmp_path, capsys)
    names = [f["name"] for f in data["top_level"]]
    assert names == ["ts", "in", "out", "cache_c", "cache_r", "cost", "inflight"]
    assert set(data["exit_codes"].keys()) == {"0", "2", "4", "8"}
    fmt_names = [f["name"] for f in data["formats"]]
    assert set(fmt_names) == {"human", "json", "prometheus"}

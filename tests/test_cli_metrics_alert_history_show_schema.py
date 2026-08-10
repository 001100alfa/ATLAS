"""SPEC 179 — atlas metrics --alert-history-show --schema testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "kesinlikle-yok.jsonl"))


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    _env(monkeypatch, tmp_path)
    rc = main([
        "metrics", "--alert-history-show",
        str(tmp_path / "yok.jsonl"),  # dosya yok — kısa devre gerekmez
        "--schema",
    ])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_179_schema_kisa_devre_log_gerekmez(monkeypatch, tmp_path, capsys):
    """--schema log dosyası olmasa da çalışır (kısa devre)."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert data["schema_version"] == "1"


def test_179_record_fields_10_zorunlu_2_opsiyonel(monkeypatch, tmp_path, capsys):
    data = _schema(monkeypatch, tmp_path, capsys)
    names = [f["name"] for f in data["record_fields"]]
    # SPEC 126 mevcut 10 alan
    for expected in ("ts", "alert", "hit_ratio_pct", "threshold_pct",
                     "records", "tokens_in", "tokens_out",
                     "cache_creation", "cache_read", "channels"):
        assert expected in names
    # SPEC 169 iki opsiyonel alan
    assert "alert_window_minutes" in names
    assert "alert_window_records" in names


def test_179_record_fields_when_kosullari(monkeypatch, tmp_path, capsys):
    """SPEC 169 alanları `when` alanında koşula bağlı."""
    data = _schema(monkeypatch, tmp_path, capsys)
    by_name = {f["name"]: f for f in data["record_fields"]}
    assert by_name["alert_window_minutes"]["spec"] == "169"
    assert "--alert-window" in by_name["alert_window_minutes"]["when"]
    assert by_name["alert_window_records"]["spec"] == "169"


def test_179_summary_fields_var(monkeypatch, tmp_path, capsys):
    """SPEC 132 --json summary satırı 4 alan."""
    data = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in data["summary_fields"]}
    assert names == {"type", "path", "count", "total"}


def test_179_exit_codes_0_2_4(monkeypatch, tmp_path, capsys):
    """SPEC 132 exit 0/2 + SPEC 148 exit 4."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert set(data["exit_codes"].keys()) == {"0", "2", "4"}


def test_179_formats_uc_secenek(monkeypatch, tmp_path, capsys):
    """human (132) + json (132) + prometheus (143)."""
    data = _schema(monkeypatch, tmp_path, capsys)
    by_name = {f["name"]: f for f in data["formats"]}
    assert by_name["human"]["spec"] == "132"
    assert by_name["json"]["spec"] == "132"
    assert by_name["prometheus"]["spec"] == "143"


def test_179_notes_spec_referanslari(monkeypatch, tmp_path, capsys):
    data = _schema(monkeypatch, tmp_path, capsys)
    notes_text = " ".join(data["notes"])
    for spec in ("126", "132", "139", "143", "144", "148", "179"):
        assert f"SPEC {spec}" in notes_text


def test_179_pretty_indent_2(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "metrics", "--alert-history-show",
        str(tmp_path / "yok.jsonl"),
        "--schema", "--pretty",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert '\n  "schema_version"' in out
    assert '\n  "record_fields"' in out


def test_179_default_path_ile_schema(monkeypatch, tmp_path, capsys):
    """--alert-history-show argümansız (default .atlas/alert-history.jsonl)
    ile --schema."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--alert-history-show", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"


def test_179_schema_normal_show_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--schema YOKSA SPEC 132 normal show davranışı AYNI (log boş)."""
    _env(monkeypatch, tmp_path)
    log = tmp_path / "yok.jsonl"
    rc = main(["metrics", "--alert-history-show", str(log)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "schema_version" not in out
    assert "ATLAS metrics --alert-history-show" in out


def test_179_metrics_schema_hala_calisir(monkeypatch, tmp_path, capsys):
    """SPEC 153 `metrics --schema` (alert-history-show olmadan) AYNI çalışır."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    # SPEC 175 alert_options alanı olmalı (SPEC 153 üstüne)
    assert "alert_options" in data
    # SPEC 179 alanları (record_fields) SPEC 153'te YOK
    assert "record_fields" not in data

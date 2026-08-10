"""SPEC 153 — atlas metrics --schema testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    # SPEC 153: dizin gerekmez ama env pointer da lazımsız test için ok
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "kesinlikle-yok.jsonl"))


def test_153_schema_kisa_devre(monkeypatch, tmp_path, capsys):
    """--schema kısa devre; metrics.jsonl gerekmez."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"


def test_153_schema_top_level_alan_sayisi(monkeypatch, tmp_path, capsys):
    """SPEC 023 record 7 alan."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [f["name"] for f in data["top_level"]]
    assert names == ["ts", "in", "out", "cache_c", "cache_r", "cost", "inflight"]


def test_153_schema_exit_codes(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    for code in ("0", "2", "4", "8"):
        assert code in data["exit_codes"]


def test_153_schema_formats(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    fmt_names = [f["name"] for f in data["formats"]]
    assert set(fmt_names) == {"human", "json", "prometheus"}


def test_153_schema_notes_spec_referanslari(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    notes_text = " ".join(data["notes"])
    for spec in ("023", "029", "043", "153"):
        assert f"SPEC {spec}" in notes_text


def test_153_schema_pretty_indent(monkeypatch, tmp_path, capsys):
    """--pretty indent=2 JSON."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--schema", "--pretty"])
    assert rc == 0
    out = capsys.readouterr().out
    # indent=2 → satır sonrası boşluk hizası
    assert '\n  "schema_version"' in out


def test_153_metrics_normal_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--schema YOKSA SPEC 023 normal davranış AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--limit", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    # metrics.jsonl yok → boş rapor beklenir; sadece exit 0 yeterli
    assert "schema_version" not in out

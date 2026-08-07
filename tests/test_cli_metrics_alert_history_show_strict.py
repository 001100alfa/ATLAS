"""SPEC 148 — atlas metrics --alert-history-show --strict testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _seed(path: Path, recs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r) for r in recs) + "\n",
        encoding="utf-8",
    )


def test_148_strict_bos_log_exit_0(monkeypatch, tmp_path, capsys):
    """Dosya yok → exit 0."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--alert-history-show", "--strict"])
    assert rc == 0


def test_148_strict_bos_dosya_exit_0(monkeypatch, tmp_path):
    """Boş dosya → exit 0."""
    _env(monkeypatch, tmp_path)
    (tmp_path / ".atlas").mkdir()
    (tmp_path / ".atlas" / "alert-history.jsonl").write_text("", encoding="utf-8")
    rc = main(["metrics", "--alert-history-show", "--strict"])
    assert rc == 0


def test_148_strict_kayit_exit_4(monkeypatch, tmp_path, capsys):
    """>=1 kayıt + --strict → exit 4 (pretty)."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main(["metrics", "--alert-history-show", "--strict"])
    assert rc == 4
    cap = capsys.readouterr()
    assert "SAĞLIK BAŞARISIZ" in cap.err
    assert "1 alert kaydı" in cap.err


def test_148_strict_json_kayit_exit_4(monkeypatch, tmp_path, capsys):
    """--json + --strict + kayıt → exit 4, JSON hâlâ basılır."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main([
        "metrics", "--alert-history-show", "--strict", "--json",
    ])
    assert rc == 4
    out = capsys.readouterr().out
    lines = [ln for ln in out.strip().split("\n") if ln.startswith("{")]
    assert len(lines) >= 1


def test_148_strict_prom_kayit_exit_4(monkeypatch, tmp_path, capsys):
    """--format prometheus + --strict + kayıt → exit 4, çıktı basılır."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus", "--strict",
    ])
    assert rc == 4
    assert "atlas_metrics_alert_history_total 1" in capsys.readouterr().out


def test_148_strict_yoksa_bit_uyumlu(monkeypatch, tmp_path):
    """--strict YOK → SPEC 132 exit 0 kayıt var da olsa."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main(["metrics", "--alert-history-show"])
    assert rc == 0

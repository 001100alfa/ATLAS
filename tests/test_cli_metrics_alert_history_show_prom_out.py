"""SPEC 144 — atlas metrics --alert-history-show --format prometheus --out PATH."""

from __future__ import annotations

import gzip
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


def test_144_out_yazma_stdout_bos(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": ["webhook"]},
    ])
    out = tmp_path / "h.prom"
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert "atlas_metrics_alert_history_" not in stdout


def test_144_out_icerik_stdout_bit_uyumlu(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": ["webhook"]},
        {"ts": "2026-08-06T15:00:00", "hit_ratio_pct": 20.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    # stdout
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
    ])
    assert rc == 0
    stdout_text = capsys.readouterr().out.strip()
    # --out
    out = tmp_path / "h.prom"
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    file_text = out.read_text(encoding="utf-8").strip()
    assert file_text == stdout_text


def test_144_out_gzip_auto_suffix(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-06T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    out = tmp_path / "h.prom"
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert not out.is_file()
    gz = tmp_path / "h.prom.gz"
    assert gz.is_file()
    with gzip.open(gz, "rt", encoding="utf-8") as fh:
        assert "atlas_metrics_alert_history_total" in fh.read()


def test_144_out_parent_auto_mkdir(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out = tmp_path / "deep" / "nested" / "h.prom"
    assert not out.parent.exists()
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()


def test_144_gzip_out_yok_mutex(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err and "--out" in err


def test_144_out_yazma_hatasi(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
        "--out", str(target),
    ])
    assert rc == 2


def test_144_out_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main([
        "metrics", "--alert-history-show", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_alert_history_total" in out

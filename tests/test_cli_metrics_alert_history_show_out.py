"""SPEC 139 — atlas metrics --alert-history-show --out PATH testleri."""

from __future__ import annotations

import gzip  # noqa: F401 — future gzip cousin
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


def test_139_out_json_yazma(monkeypatch, tmp_path, capsys):
    """--out --json → dosya, stdout NDJSON basmaz."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    out = tmp_path / "r.jsonl"
    rc = main([
        "metrics", "--alert-history-show", "--json", "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert not stdout.strip().startswith("{")


def test_139_out_json_yok_mutex(monkeypatch, tmp_path, capsys):
    """--out --json yok → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    out = tmp_path / "r.jsonl"
    rc = main([
        "metrics", "--alert-history-show", "--out", str(out),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err
    assert "--json" in err


def test_139_out_icerik_stdout_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """Dosya içeriği stdout --json modu ile AYNI."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": ["webhook"]},
        {"ts": "2026-08-05T15:00:00", "hit_ratio_pct": 20.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    # stdout --json
    rc = main(["metrics", "--alert-history-show", "--json"])
    assert rc == 0
    stdout_lines = capsys.readouterr().out.strip().split("\n")
    # --out
    out = tmp_path / "r.jsonl"
    rc = main([
        "metrics", "--alert-history-show", "--json", "--out", str(out),
    ])
    assert rc == 0
    file_lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert file_lines == stdout_lines


def test_139_out_parent_auto_mkdir(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    out = tmp_path / "deep" / "nested" / "r.jsonl"
    assert not out.parent.exists()
    rc = main([
        "metrics", "--alert-history-show", "--json", "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()


def test_139_out_yazma_hatasi_exit_2(monkeypatch, tmp_path, capsys):
    """PATH = mevcut dizin → yazma hatası exit 2."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "metrics", "--alert-history-show", "--json", "--out", str(target),
    ])
    assert rc == 2


def test_139_out_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--out YOK → SPEC 132 stdout AYNI."""
    _env(monkeypatch, tmp_path)
    history = tmp_path / ".atlas" / "alert-history.jsonl"
    _seed(history, [
        {"ts": "2026-08-05T14:00:00", "hit_ratio_pct": 10.0,
         "threshold_pct": 50.0, "channels": []},
    ])
    rc = main(["metrics", "--alert-history-show", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    lines = out.strip().split("\n")
    assert len(lines) == 2  # rec + summary

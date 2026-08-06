"""SPEC 133 — atlas archive --restore <id> --json-lines testleri."""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _make_archive(archive_root: Path, task_id: str, date: str) -> Path:
    archive_root.mkdir(parents=True, exist_ok=True)
    p = archive_root / f"{task_id}-{date}.tar.gz"
    with tarfile.open(p, "w:gz") as tar:
        info = tarfile.TarInfo(name=f"{task_id}/00-need.md")
        info.size = 5
        tar.addfile(info, fileobj=io.BytesIO(b"need\n"))
    return p


def test_133_dry_run_jsonl(monkeypatch, tmp_path, capsys):
    """--json-lines dry-run → plan + summary satırları."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-001", "2026-08-01")
    rc = main([
        "archive", "--restore", "task-001", "--json-lines",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 2
    plan = json.loads(lines[0])
    summary = json.loads(lines[1])
    assert plan["type"] == "plan"
    assert plan["task_id"] == "task-001"
    assert plan["conflict"] is False
    assert summary["type"] == "summary"
    assert summary["mode"] == "dry-run"


def test_133_apply_jsonl(monkeypatch, tmp_path, capsys):
    """--json-lines --apply → plan + restored + summary."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-002", "2026-08-01")
    rc = main([
        "archive", "--restore", "task-002", "--json-lines", "--apply",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 3
    parsed = [json.loads(ln) for ln in lines]
    assert parsed[0]["type"] == "plan"
    assert parsed[1]["type"] == "restored"
    assert parsed[2]["type"] == "summary"
    assert parsed[2]["mode"] == "apply"
    assert parsed[2]["restored"] is True
    assert (tmp_path / "pipeline" / "tasks" / "task-002" / "00-need.md").is_file()


def test_133_json_jsonl_mutex(monkeypatch, tmp_path, capsys):
    """--json + --json-lines → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-003", "2026-08-01")
    rc = main([
        "archive", "--restore", "task-003", "--json", "--json-lines",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MUTEX" in err or "birlikte" in err


def test_133_hata_jsonl_basmaz(monkeypatch, tmp_path, capsys):
    """Arşiv yok → stderr SPEC HATASI, JSON basmaz, rc 6."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    arc.mkdir()
    rc = main([
        "archive", "--restore", "task-yok", "--json-lines",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 6


def test_133_jsonl_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--json-lines YOKSA SPEC 033/127 davranışı AYNI (pretty dry-run)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-004", "2026-08-01")
    rc = main([
        "archive", "--restore", "task-004",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[dry-run]" in out

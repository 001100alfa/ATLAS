"""SPEC 127 — atlas archive --restore <id> --json testleri."""

from __future__ import annotations

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
        tar.addfile(info, fileobj=__import__("io").BytesIO(b"need\n"))
    return p


def test_127_dry_run_json(monkeypatch, tmp_path, capsys):
    """--json dry-run → {mode:dry-run,task_id,archive,target,conflict}."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-001", "2026-08-01")
    rc = main([
        "archive", "--restore", "task-001", "--json",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["mode"] == "dry-run"
    assert data["task_id"] == "task-001"
    assert "task-001-2026-08-01" in data["archive"]
    assert data["conflict"] is False


def test_127_dry_run_json_conflict_true(monkeypatch, tmp_path, capsys):
    """Hedef mevcutsa conflict=True."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-002", "2026-08-01")
    (tmp_path / "pipeline" / "tasks" / "task-002").mkdir(parents=True)
    rc = main([
        "archive", "--restore", "task-002", "--json",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["conflict"] is True


def test_127_apply_json(monkeypatch, tmp_path, capsys):
    """--apply --json → {mode:apply,task_id,archive,target,restored:true}."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-003", "2026-08-01")
    rc = main([
        "archive", "--restore", "task-003", "--json", "--apply",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["mode"] == "apply"
    assert data["restored"] is True
    assert (tmp_path / "pipeline" / "tasks" / "task-003" / "00-need.md").is_file()


def test_127_dry_run_default_pretty_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--json YOK → SPEC 033 pretty çıktı AYNI."""
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
    assert "Uygulamak için:" in out


def test_127_hata_json_basmaz(monkeypatch, tmp_path, capsys):
    """Arşiv yok → JSON basmaz, stderr'e SPEC HATASI + rc 6."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    arc.mkdir()
    rc = main([
        "archive", "--restore", "task-yok", "--json",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "ARŞİV HATASI" in err

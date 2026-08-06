"""SPEC 138 — atlas archive --restore <id> --json-lines --out PATH testleri."""

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


def test_138_dry_run_jsonl_out_yazma(monkeypatch, tmp_path, capsys):
    """Dry-run --json-lines --out → dosya, stdout NDJSON basmaz."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-138a", "2026-08-06")
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--restore", "task-138a", "--json-lines", "--out", str(out),
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert not stdout.strip().startswith("{")
    lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["type"] == "plan"
    assert json.loads(lines[1])["type"] == "summary"


def test_138_apply_jsonl_out_yazma(monkeypatch, tmp_path, capsys):
    """--apply --json-lines --out → 3 satır (plan+restored+summary)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-138b", "2026-08-06")
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--restore", "task-138b", "--json-lines", "--out", str(out),
        "--apply",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.is_file()
    lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    types = [json.loads(ln)["type"] for ln in lines]
    assert types == ["plan", "restored", "summary"]
    assert (tmp_path / "pipeline" / "tasks" / "task-138b" / "00-need.md").is_file()


def test_138_out_bit_uyumlu_stdout(monkeypatch, tmp_path, capsys):
    """Dosya içeriği stdout modu ile AYNI."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-138c", "2026-08-06")
    # stdout
    rc = main([
        "archive", "--restore", "task-138c", "--json-lines",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    stdout_lines = capsys.readouterr().out.strip().split("\n")
    # --out
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--restore", "task-138c", "--json-lines", "--out", str(out),
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    file_lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert file_lines == stdout_lines


def test_138_out_json_mode_mutex(monkeypatch, tmp_path, capsys):
    """--out --json (tek JSON, jsonl yok) → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-138d", "2026-08-06")
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--restore", "task-138d", "--json", "--out", str(out),
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err
    assert "--json-lines" in err


def test_138_out_parent_auto_mkdir(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-138e", "2026-08-06")
    out = tmp_path / "deep" / "nested" / "r.jsonl"
    assert not out.parent.exists()
    rc = main([
        "archive", "--restore", "task-138e", "--json-lines", "--out", str(out),
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.is_file()


def test_138_out_yazma_hatasi(monkeypatch, tmp_path, capsys):
    """PATH = dizin → yazma hatası exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-138f", "2026-08-06")
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "archive", "--restore", "task-138f", "--json-lines", "--out", str(target),
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 2


def test_138_hata_dosya_yazilmaz(monkeypatch, tmp_path):
    """Arşiv yok → dosya YAZILMAZ, rc 6."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    arc.mkdir()
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--restore", "task-yok", "--json-lines", "--out", str(out),
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 6
    assert not out.exists()


def test_138_out_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--out YOKSA SPEC 133 stdout AYNI."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _make_archive(arc, "task-138g", "2026-08-06")
    rc = main([
        "archive", "--restore", "task-138g", "--json-lines",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[-1])["type"] == "summary"

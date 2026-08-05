"""SPEC 075 — atlas archive --list metadata listesi."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import _list_archive_entries, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _mktar(arc: Path, name: str, members: list[str]) -> Path:
    arc.mkdir(parents=True, exist_ok=True)
    tar_path = arc / name
    with tarfile.open(tar_path, "w:gz") as tar:
        for m in members:
            info = tarfile.TarInfo(name=m)
            info.size = 0
            tar.addfile(info)
    return tar_path


# ═════════════════════════════════════════════════════════════════════
# _list_archive_entries (birim)
# ═════════════════════════════════════════════════════════════════════


def test_075_list_arsiv_yok(tmp_path: Path) -> None:
    assert _list_archive_entries(tmp_path / "yok") == []


def test_075_list_bos_arsiv(tmp_path: Path) -> None:
    arc = tmp_path / "arc"
    arc.mkdir()
    assert _list_archive_entries(arc) == []


def test_075_list_task_id_date_ayirir(tmp_path: Path) -> None:
    """`<task_id>-YYYY-MM-DD.tar.gz` → task_id ve date ayrı."""
    arc = tmp_path / "arc"
    _mktar(arc, "task-042-2026-08-05.tar.gz", ["task-042/a.md"])
    entries = _list_archive_entries(arc)
    assert len(entries) == 1
    e = entries[0]
    assert e["archive"] == "task-042-2026-08-05.tar.gz"
    assert e["task_id"] == "task-042"
    assert e["date"] == "2026-08-05"
    assert e["member_count"] == 1
    assert e["size_bytes"] > 0
    assert "B" in e["size_human"] or "KB" in e["size_human"]


def test_075_list_atipik_format_fallback_stem(tmp_path: Path) -> None:
    """Format `<x>-YYYY-MM-DD` değilse → task_id = stem, date = ""."""
    arc = tmp_path / "arc"
    _mktar(arc, "backup-final.tar.gz", ["x"])
    entries = _list_archive_entries(arc)
    assert len(entries) == 1
    assert entries[0]["task_id"] == "backup-final"
    assert entries[0]["date"] == ""


def test_075_list_coklu_arsiv_alfabetik_sira(tmp_path: Path) -> None:
    arc = tmp_path / "arc"
    _mktar(arc, "zzz-2026-01-01.tar.gz", ["z"])
    _mktar(arc, "aaa-2026-01-01.tar.gz", ["a"])
    _mktar(arc, "mmm-2026-01-01.tar.gz", ["m"])
    entries = _list_archive_entries(arc)
    names = [e["archive"] for e in entries]
    assert names == sorted(names)


def test_075_list_bozuk_tar_atlar(tmp_path: Path) -> None:
    """Bozuk `.tar.gz` → member_count=-1 (best-effort)."""
    arc = tmp_path / "arc"
    _mktar(arc, "iyi-2026-08-05.tar.gz", ["a"])
    bad = arc / "bozuk-2026-08-05.tar.gz"
    bad.write_bytes(b"not tar")
    entries = _list_archive_entries(arc)
    assert len(entries) == 2
    good = next(e for e in entries if e["task_id"] == "iyi")
    bad_e = next(e for e in entries if e["task_id"] == "bozuk")
    assert good["member_count"] == 1
    assert bad_e["member_count"] == -1


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas archive --list
# ═════════════════════════════════════════════════════════════════════


def test_075_cli_list_arc_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main([
        "archive", "--list",
        "--archive-root", str(tmp_path / "yok"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_075_cli_list_insan_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    _mktar(tmp_path / "arc", "task-042-2026-08-05.tar.gz",
           ["task-042/09-ship.md", "task-042/src/x.py"])
    rc = main([
        "archive", "--list",
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 arsiv" in out
    assert "task-042" in out
    assert "2026-08-05" in out
    assert "2 uye" in out or "2 üye" in out


def test_075_cli_list_bos_mesaj(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    (tmp_path / "arc").mkdir()
    rc = main([
        "archive", "--list",
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(arsiv yok)" in out


def test_075_cli_list_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    _mktar(tmp_path / "arc", "task-042-2026-08-05.tar.gz",
           ["task-042/a.md", "task-042/b.md"])
    rc = main([
        "archive", "--list", "--json",
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 1
    e = data[0]
    assert e["task_id"] == "task-042"
    assert e["date"] == "2026-08-05"
    assert e["member_count"] == 2
    assert e["size_bytes"] > 0
    assert "size_human" in e
    assert "mtime" in e


def test_075_cli_archive_diger_modlari_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--list yoksa mevcut davranış (task yok hatası)."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "<task> ya da --all ya da --restore" in err

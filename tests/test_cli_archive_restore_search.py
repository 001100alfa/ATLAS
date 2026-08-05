"""SPEC 071 — atlas archive --restore --search PATTERN birleşim testleri."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _mkarchive(archive_root: Path, task_id: str, files: dict[str, str]) -> Path:
    """`<task_id>-YYYY-MM-DD.tar.gz` üret; içine gerçek dosyalar."""
    from datetime import date
    archive_root.mkdir(parents=True, exist_ok=True)
    tar_path = archive_root / f"{task_id}-{date.today().isoformat()}.tar.gz"
    # Geçici dizin — tar.add için
    src_dir = archive_root.parent / f".src-{task_id}"
    src_dir.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        p = src_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(src_dir, arcname=task_id)
    import shutil
    shutil.rmtree(src_dir)
    return tar_path


# ═════════════════════════════════════════════════════════════════════
# CLI: --restore --search PATTERN
# ═════════════════════════════════════════════════════════════════════


def test_071_cli_restore_search_tek_eslesme_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--restore --search tek eşleşme → dry-run planı task_id çıkarır."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    tasks = tmp_path / "tasks"
    _mkarchive(arc, "task-042", {"09-ship.md": "spec 042"})

    rc = main([
        "archive", "--restore", "--search", r"09-ship",
        "--archive-root", str(arc),
        "--tasks-root", str(tasks),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "task-042" in out


def test_071_cli_restore_search_tek_eslesme_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--restore --search --apply → gerçek restore."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    tasks = tmp_path / "tasks"
    _mkarchive(arc, "task-042", {
        "09-ship.md": "spec 042 tamam",
        "src/x.py": "print(1)",
    })

    rc = main([
        "archive", "--restore", "--search", r"09-ship",
        "--apply",
        "--archive-root", str(arc),
        "--tasks-root", str(tasks),
    ])
    assert rc == 0
    # Restore doğrulama
    assert (tasks / "task-042" / "09-ship.md").read_text(encoding="utf-8") == "spec 042 tamam"
    assert (tasks / "task-042" / "src" / "x.py").is_file()
    # Audit
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "restore" in audit


def test_071_cli_restore_search_bulgu_yok_exit_6(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mkarchive(arc, "task-x", {"a.md": "x"})

    rc = main([
        "archive", "--restore", "--search", "zzz-hicbir-sey",
        "--archive-root", str(arc),
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "hiç eşleşme" in err


def test_071_cli_restore_search_coklu_eslesme_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """2+ arşiv eşleşirse → exit 2 SPEC HATASI (belirsizlik)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mkarchive(arc, "task-A", {"09-ship.md": "A"})
    _mkarchive(arc, "task-B", {"09-ship.md": "B"})

    rc = main([
        "archive", "--restore", "--search", r"09-ship",
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "belirsiz" in err
    assert "task-A" in err
    assert "task-B" in err


def test_071_cli_restore_search_regex_gecersiz_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    arc.mkdir()
    rc = main([
        "archive", "--restore", "--search", "[bad(",
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "regex hatası" in err


def test_071_cli_restore_id_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--restore <id>` (search yok) mevcut SPEC 033 davranış."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    tasks = tmp_path / "tasks"
    _mkarchive(arc, "task-042", {"09-ship.md": "ok"})

    rc = main([
        "archive", "--restore", "task-042", "--apply",
        "--archive-root", str(arc),
        "--tasks-root", str(tasks),
    ])
    assert rc == 0
    assert (tasks / "task-042" / "09-ship.md").is_file()


def test_071_cli_search_only_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--search PATTERN` (restore yok) mevcut SPEC 065 list davranış."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mkarchive(arc, "task-042", {"09-ship.md": "ok"})

    rc = main([
        "archive", "--search", r"09-ship",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # SPEC 065 insan çıktısı
    assert "arsivde" in out or "eslesme" in out

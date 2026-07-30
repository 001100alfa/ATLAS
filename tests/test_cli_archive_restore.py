"""SPEC 033 — atlas archive --restore <id> testleri."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.archive import (
    RestoreError,
    _find_archive_for_task,
    restore_task,
)


def _make_archive(archive_root: Path, task_id: str, files: dict[str, str]) -> Path:
    """Verilen (relatif yol → içerik) dict'ini `<task_id>/` altında
    tar.gz'e sarmalar. `<archive_root>/<task_id>-2026-07-30.tar.gz` döner.
    """
    archive_root.mkdir(parents=True, exist_ok=True)
    src = archive_root.parent / "_scratch" / task_id
    src.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    tar_path = archive_root / f"{task_id}-2026-07-30.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(src, arcname=task_id)
    # kaynak scratch'ı temizle
    import shutil
    shutil.rmtree(src.parent)
    return tar_path


# ═════════════════════════════════════════════════════════════════════
# restore_task — birim
# ═════════════════════════════════════════════════════════════════════


def test_033_find_archive_yok(tmp_path: Path) -> None:
    assert _find_archive_for_task(tmp_path / "yok", "003") is None
    (tmp_path / "arc").mkdir()
    assert _find_archive_for_task(tmp_path / "arc", "003") is None


def test_033_find_archive_en_yeni_secilir(tmp_path: Path) -> None:
    """Aynı task_id için iki tar → en yeni mtime seçilir."""
    arc = tmp_path / "arc"
    p1 = _make_archive(arc, "003", {"a.md": "A"})
    # ikinci tar'ı elle mtime ile geleceğe koy
    p2 = arc / "003-2026-08-01.tar.gz"
    p1.rename(p2)  # rename → aynı içerik, yeni ad
    p1_new = _make_archive(arc, "003", {"a.md": "AA"})
    import os
    # p2'nin mtime'ını daha yeni yap
    os.utime(p2, (p1_new.stat().st_mtime + 100, p1_new.stat().st_mtime + 100))

    found = _find_archive_for_task(arc, "003")
    assert found == p2


def test_033_restore_task_basari(tmp_path: Path) -> None:
    """Sağlıklı arşiv → pipeline/tasks altında geri yüklenir."""
    arc = tmp_path / "archive"
    tasks = tmp_path / "tasks"
    _make_archive(arc, "003", {"00-need.md": "need", "09-ship.md": "ship"})

    tar_out, restored = restore_task("003", arc, tasks)
    assert restored == tasks / "003"
    assert (restored / "00-need.md").read_text(encoding="utf-8") == "need"
    assert (restored / "09-ship.md").read_text(encoding="utf-8") == "ship"
    assert tar_out.name.startswith("003-")


def test_033_restore_arsiv_yok(tmp_path: Path) -> None:
    arc = tmp_path / "arc"
    arc.mkdir()
    tasks = tmp_path / "tasks"
    with pytest.raises(RestoreError, match="arşiv bulunamadı"):
        restore_task("003", arc, tasks)


def test_033_restore_hedef_zaten_var(tmp_path: Path) -> None:
    arc = tmp_path / "arc"
    tasks = tmp_path / "tasks"
    _make_archive(arc, "003", {"x.md": "x"})
    (tasks / "003").mkdir(parents=True)
    with pytest.raises(RestoreError, match="zaten var"):
        restore_task("003", arc, tasks)


def test_033_restore_path_traversal_reddedilir(tmp_path: Path) -> None:
    """Kötücül tar (../evil) reddedilir."""
    arc = tmp_path / "arc"
    arc.mkdir()
    tasks = tmp_path / "tasks"
    bad = arc / "003-2026-07-30.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        info = tarfile.TarInfo(name="../evil.txt")
        info.size = 0
        tar.addfile(info)

    with pytest.raises(RestoreError, match="güvensiz"):
        restore_task("003", arc, tasks)
    # Hedef klasör oluşmamalı
    assert not (tasks / "003").exists()


def test_033_restore_kolon_reddedilir(tmp_path: Path) -> None:
    """Windows NTFS ADS (`file:stream`) reddedilir."""
    arc = tmp_path / "arc"
    arc.mkdir()
    tasks = tmp_path / "tasks"
    bad = arc / "003-2026-07-30.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        info = tarfile.TarInfo(name="003/file:stream")
        info.size = 0
        tar.addfile(info)

    with pytest.raises(RestoreError, match="kolon"):
        restore_task("003", arc, tasks)


def test_033_restore_beklenmeyen_kok_reddedilir(tmp_path: Path) -> None:
    """Tar kökü `<task_id>` değilse reddedilir."""
    arc = tmp_path / "arc"
    arc.mkdir()
    tasks = tmp_path / "tasks"
    bad = arc / "003-2026-07-30.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        info = tarfile.TarInfo(name="baska-kok/file.md")
        info.size = 0
        tar.addfile(info)

    with pytest.raises(RestoreError, match="beklenmeyen kök"):
        restore_task("003", arc, tasks)


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas archive --restore
# ═════════════════════════════════════════════════════════════════════


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "vault"))


def test_033_cli_dry_run_plan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--restore <id>` (apply yok) → dry-run planı."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "archive"
    tasks = tmp_path / "tasks"
    _make_archive(arc, "003", {"x.md": "x"})

    rc = main([
        "archive", "--restore", "003",
        "--tasks-root", str(tasks),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "003-2026-07-30.tar.gz" in out
    assert "Uygulamak için: atlas archive --restore 003 --apply" in out
    # Dry-run → dosya yazılmadı
    assert not (tasks / "003").exists()


def test_033_cli_apply_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--restore <id> --apply` → geri açar, audit yazar."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "archive"
    tasks = tmp_path / "tasks"
    _make_archive(arc, "003", {"00-need.md": "need\n"})

    rc = main([
        "archive", "--restore", "003", "--apply",
        "--tasks-root", str(tasks),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert (tasks / "003" / "00-need.md").read_text(encoding="utf-8") == "need\n"
    out = capsys.readouterr().out
    assert "geri yüklendi:" in out
    # Audit satırı
    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "restore" in audit_txt
    assert "003" in audit_txt


def test_033_cli_arsiv_yok_exit_6(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--restore <id>` arşiv yoksa exit 6."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "archive"
    arc.mkdir()
    tasks = tmp_path / "tasks"

    rc = main([
        "archive", "--restore", "yok",
        "--tasks-root", str(tasks),
        "--archive-root", str(arc),
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "arşiv bulunamadı" in err


def test_033_cli_hedef_var_exit_3(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--restore --apply` çakışma → exit 3."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "archive"
    tasks = tmp_path / "tasks"
    _make_archive(arc, "003", {"x.md": "x"})
    (tasks / "003").mkdir(parents=True)  # çakışma

    rc = main([
        "archive", "--restore", "003", "--apply",
        "--tasks-root", str(tasks),
        "--archive-root", str(arc),
    ])
    assert rc == 3
    err = capsys.readouterr().err
    assert "zaten var" in err

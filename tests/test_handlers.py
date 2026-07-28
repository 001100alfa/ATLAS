"""004 — handler birim testleri."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from atlas_core.workflows.handlers._errors import HandlerError
from atlas_core.workflows.handlers.archive import make_archive_handler
from atlas_core.workflows.handlers.gate import make_gate_handler
from atlas_core.workflows.handlers.test import make_test_handler

# --- gate ---

def test_gate_dosya_var(tmp_path: Path) -> None:
    p = tmp_path / "a.md"
    p.write_text("x")
    h = make_gate_handler()
    assert "GEÇTİ" in h({"file": str(p)})


def test_gate_dosya_yok(tmp_path: Path) -> None:
    h = make_gate_handler()
    with pytest.raises(HandlerError, match="dosya yok"):
        h({"file": str(tmp_path / "yok.md")})


def test_gate_file_parametresi_eksik() -> None:
    h = make_gate_handler()
    with pytest.raises(HandlerError, match="'file' parametresi"):
        h({})


# --- test ---

def test_pytest_dry_run() -> None:
    h = make_test_handler(dry_run=True)
    out = h({"paths": ["tests/test_goals.py"]})
    assert out.startswith("[dry-run]")
    assert "pytest" in out


def test_pytest_gercek_kucuk_kosu() -> None:
    h = make_test_handler(dry_run=False)
    out = h({"paths": ["tests/test_goals.py"]})
    assert "pytest OK" in out


def test_pytest_hata_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    # Yapay bir başarısız pytest komutu: --hatalıbayrak
    class _Proc:
        returncode = 2
        stdout = "usage: pytest\npytest: error: unrecognized arguments: --hatalibayrak"
        stderr = ""

    def fake_run(*_a: object, **_k: object) -> _Proc:
        return _Proc()

    monkeypatch.setattr(subprocess, "run", fake_run)
    h = make_test_handler(dry_run=False)
    with pytest.raises(HandlerError, match="exit=2"):
        h({"paths": ["tests"]})


def test_pytest_paths_tipi_hatali() -> None:
    h = make_test_handler(dry_run=True)
    with pytest.raises(HandlerError, match="'paths'"):
        h({"paths": "tests"})


# --- archive ---

def test_archive_dry_run_dosyaya_dokunmaz(tmp_path: Path) -> None:
    tasks = tmp_path / "pipeline" / "tasks"
    task = tasks / "999-demo"
    task.mkdir(parents=True)
    (task / "note.md").write_text("içerik")
    h = make_archive_handler(
        tasks_root=tasks, archive_root=tmp_path / "arch", vault_root=tmp_path / "v",
        dry_run=True,
    )
    out = h({"task": "999-demo"})
    assert "[dry-run]" in out
    assert task.exists()  # silinmedi


def test_archive_gercek_yazar(tmp_path: Path) -> None:
    tasks = tmp_path / "pipeline" / "tasks"
    task = tasks / "999-demo"
    task.mkdir(parents=True)
    (task / "n.md").write_text("x")
    h = make_archive_handler(
        tasks_root=tasks, archive_root=tmp_path / "arch", vault_root=tmp_path / "v",
        dry_run=False,
    )
    out = h({"task": "999-demo"})
    assert "arşivlendi" in out
    assert not task.exists()  # rmtree yapıldı
    assert any((tmp_path / "arch").iterdir())


def test_archive_task_dizini_yok(tmp_path: Path) -> None:
    h = make_archive_handler(tasks_root=tmp_path, archive_root=tmp_path, vault_root=tmp_path)
    with pytest.raises(HandlerError, match="görev klasörü yok"):
        h({"task": "hic-yok"})


def test_archive_task_parametresi_eksik(tmp_path: Path) -> None:
    h = make_archive_handler(tasks_root=tmp_path, archive_root=tmp_path, vault_root=tmp_path)
    with pytest.raises(HandlerError, match="'task' parametresi"):
        h({})


def test_yaml_dry_run_handler_default_ezer(tmp_path: Path) -> None:
    tasks = tmp_path / "t"
    (tasks / "x").mkdir(parents=True)
    (tasks / "x" / "a.md").write_text("y")
    # handler default dry_run=True, ama YAML dry_run=False kazanır
    h = make_archive_handler(
        tasks_root=tasks, archive_root=tmp_path / "a", vault_root=tmp_path / "v",
        dry_run=True,
    )
    out = h({"task": "x", "dry_run": False})
    assert "arşivlendi" in out


_ = sys  # ruff unused-import guard

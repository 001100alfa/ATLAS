"""004 — `atlas workflow run` e2e testleri."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run(*args: str, env_extra: dict[str, str] | None = None,
         cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    # DECISIONS 2026-07-24 kalıbı: cp1254 locale'da UTF-8 çıktıyı reader thread
    # decode edemiyor → encoding sabit + errors="replace".
    return subprocess.run(
        [sys.executable, "-m", "atlas_core.cli", *args],
        capture_output=True, text=True, env=env, cwd=cwd, timeout=300,
        encoding="utf-8", errors="replace",
    )


def test_workflow_mini_happy(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    proc = _run(
        "workflow", "run", "tests/workflows/mini.yaml",
        env_extra={"ATLAS_AUDIT": str(audit)},
    )
    assert proc.returncode == 0, proc.stderr
    assert "3 adım" in proc.stdout
    lines = audit.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 3


def test_workflow_bilinmeyen_handler(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: b\nsteps:\n  - uses: bogus.step\n", encoding="utf-8")
    proc = _run(
        "workflow", "run", str(bad),
        env_extra={"ATLAS_AUDIT": str(tmp_path / "a.jsonl")},
    )
    assert proc.returncode == 6
    assert "WORKFLOW HATASI" in proc.stderr


def test_workflow_gate_basarisiz(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "name: b\nsteps:\n"
        "  - uses: pipeline.gate\n    with: {file: yok/olmayan.md}\n"
        "  - uses: pipeline.gate\n    with: {file: pyproject.toml}\n",
        encoding="utf-8",
    )
    audit = tmp_path / "a.jsonl"
    proc = _run("workflow", "run", str(bad), env_extra={"ATLAS_AUDIT": str(audit)})
    assert proc.returncode == 6
    assert "HANDLER HATASI" in proc.stderr
    # sadece error kaydı; ikinci gate çalışmadı
    content = audit.read_text(encoding="utf-8")
    assert "error" in content
    assert content.count("pipeline.gate") <= 1  # sadece hata satırı


def test_workflow_yaml_yok(tmp_path: Path) -> None:
    proc = _run(
        "workflow", "run", str(tmp_path / "yok.yaml"),
        env_extra={"ATLAS_AUDIT": str(tmp_path / "a.jsonl")},
    )
    assert proc.returncode == 2
    assert "SPEC HATASI" in proc.stderr


def test_workflow_dry_run_pytest_calismaz(tmp_path: Path) -> None:
    y = tmp_path / "d.yaml"
    y.write_text(
        "name: d\nsteps:\n"
        "  - uses: pipeline.test\n    with: {paths: [tests/test_goals.py]}\n",
        encoding="utf-8",
    )
    proc = _run(
        "workflow", "run", str(y), "--dry-run",
        env_extra={"ATLAS_AUDIT": str(tmp_path / "a.jsonl")},
    )
    assert proc.returncode == 0
    assert "[dry-run]" in proc.stdout


def test_workflow_audit_verify(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    _run("workflow", "run", "tests/workflows/mini.yaml",
         env_extra={"ATLAS_AUDIT": str(audit)})
    verify = _run("audit-verify", env_extra={"ATLAS_AUDIT": str(audit)})
    assert verify.returncode == 0
    assert "GEÇERLİ" in verify.stdout

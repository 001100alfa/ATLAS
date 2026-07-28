"""SPEC 002 §2 (CLI arayüzü) — `atlas run --goal-file` testleri (Adım 3.5)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "goals"


def _run(*args: str, env_extra: dict[str, str] | None = None,
         cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    import os
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "atlas_core.cli", *args],
        capture_output=True, text=True, env=env, cwd=cwd, timeout=30,
    )


def test_run_goal_file_hello(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    sandbox_root = tmp_path / "sb"
    proc = _run(
        "run", "--goal-file", str(FIXTURES / "hello.yaml"), "--run-id", "test",
        env_extra={"ATLAS_AUDIT": str(audit), "ATLAS_SANDBOX": str(sandbox_root)},
    )
    assert proc.returncode == 0, proc.stderr
    assert (sandbox_root / "hello-test" / "hello.txt").read_text(encoding="utf-8") == "merhaba"
    lines = audit.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 3  # plan + observe + done


def test_run_eski_pozitif_regresyon(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    proc = _run(
        "run", "eski hedef", "--steps", "1", "--budget", "50", "--step-cost", "5",
        env_extra={"ATLAS_AUDIT": str(audit)},
    )
    assert proc.returncode == 0, proc.stderr
    assert "done=True" in proc.stdout


def test_run_ne_goal_ne_file(tmp_path: Path) -> None:
    proc = _run("run", env_extra={"ATLAS_AUDIT": str(tmp_path / "a.jsonl")})
    assert proc.returncode == 2
    assert "kullanım" in proc.stderr


def test_run_spec_hatasi(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("plan_kind: static\n", encoding="utf-8")  # eksik goal
    proc = _run(
        "run", "--goal-file", str(bad),
        env_extra={"ATLAS_AUDIT": str(tmp_path / "a.jsonl"),
                   "ATLAS_SANDBOX": str(tmp_path / "sb")},
    )
    assert proc.returncode == 2
    assert "SPEC HATASI" in proc.stderr


@pytest.mark.parametrize(
    "fixture,expected_exit",
    [
        ("denied_verb.yaml", 5),
        ("denied_shell.yaml", 5),
        ("escape.yaml", 5),
    ],
)
def test_run_deny_senaryolari(tmp_path: Path, fixture: str, expected_exit: int) -> None:
    audit = tmp_path / "audit.jsonl"
    proc = _run(
        "run", "--goal-file", str(FIXTURES / fixture), "--run-id", "t",
        env_extra={"ATLAS_AUDIT": str(audit), "ATLAS_SANDBOX": str(tmp_path / "sb")},
    )
    assert proc.returncode == expected_exit, proc.stderr
    # denied kaydı audit'te
    assert "denied" in audit.read_text(encoding="utf-8")
    # sandbox parent'ında escape.txt oluşmamış (AC4)
    assert not (tmp_path / "sb" / "escape.txt").exists()
    assert not (tmp_path / "escape.txt").exists()


def test_run_butce_asimi(tmp_path: Path) -> None:
    proc = _run(
        "run", "--goal-file", str(FIXTURES / "budget.yaml"), "--run-id", "t",
        env_extra={"ATLAS_AUDIT": str(tmp_path / "a.jsonl"),
                   "ATLAS_SANDBOX": str(tmp_path / "sb")},
    )
    assert proc.returncode == 3, proc.stderr
    assert "BÜTÇE" in proc.stderr


def test_run_llm_stub_max_steps(tmp_path: Path) -> None:
    proc = _run(
        "run", "--goal-file", str(FIXTURES / "llm_stub.yaml"), "--run-id", "t",
        env_extra={"ATLAS_AUDIT": str(tmp_path / "a.jsonl"),
                   "ATLAS_SANDBOX": str(tmp_path / "sb"),
                   "ATLAS_LLM": "stub"},
    )
    # plan[stub]:noop -> action "plan[stub]" verb → ActionDenied (fiil yok)
    # yani exit 5 beklenir (fiil izinli değil)
    assert proc.returncode == 5, proc.stderr


def test_run_audit_verify_gecerli(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    sandbox_root = tmp_path / "sb"
    _run("run", "--goal-file", str(FIXTURES / "hello.yaml"), "--run-id", "t",
         env_extra={"ATLAS_AUDIT": str(audit), "ATLAS_SANDBOX": str(sandbox_root)})
    verify = _run("audit-verify", env_extra={"ATLAS_AUDIT": str(audit)})
    assert verify.returncode == 0
    assert "GEÇERLİ" in verify.stdout

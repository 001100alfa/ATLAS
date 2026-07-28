"""SPEC 002 §3 (FR5) — Judge testleri (Adım 3.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal
from atlas_core.orchestrator.judges import make_judge


def _goal(judge_kind: str, judge_arg: str) -> Goal:
    return Goal(
        goal="t",
        plan_kind="static",
        plan_steps=("read:x",),
        action_allowlist=frozenset({"read"}),
        shell_allow_regex=None,
        judge_kind=judge_kind,  # type: ignore[arg-type]
        judge_arg=judge_arg,
        budget=10.0,
        max_steps=5,
        costs={"read": 1.0, "write": 2.0, "shell": 5.0},
    )


# file_exists
def test_file_exists_pozitif(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x")
    j = make_judge(_goal("file_exists", "a.txt"), tmp_path, {})
    assert j([]) is True


def test_file_exists_negatif(tmp_path: Path) -> None:
    j = make_judge(_goal("file_exists", "yok.txt"), tmp_path, {})
    assert j([]) is False


# regex_in_last_observe
def test_regex_son_observe_eslesir(tmp_path: Path) -> None:
    j = make_judge(_goal("regex_in_last_observe", r"exit=0"), tmp_path, {})
    hist = [
        (StepKind.PLAN, "p1"),
        (StepKind.OBSERVE, "exit=1 error"),
        (StepKind.PLAN, "p2"),
        (StepKind.OBSERVE, "exit=0 ok"),
    ]
    assert j(hist) is True


def test_regex_son_observe_eslesmez(tmp_path: Path) -> None:
    j = make_judge(_goal("regex_in_last_observe", r"success"), tmp_path, {})
    hist = [(StepKind.OBSERVE, "failure only")]
    assert j(hist) is False


# exit_zero
def test_exit_zero_pozitif(tmp_path: Path) -> None:
    exit_map = {"shell": 0}
    j = make_judge(_goal("exit_zero", ""), tmp_path, exit_map)
    assert j([]) is True


def test_exit_zero_negatif(tmp_path: Path) -> None:
    exit_map = {"shell": 1}
    j = make_judge(_goal("exit_zero", ""), tmp_path, exit_map)
    assert j([]) is False


def test_bilinmeyen_judge_kind(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bilinmeyen judge_kind"):
        make_judge(_goal("wat", ""), tmp_path, {})  # type: ignore[arg-type]

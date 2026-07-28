"""Judge fabrikaları — file_exists / regex_in_last_observe / exit_zero.

SPEC 002 §3 (FR5). `run_loop`'un beklediği Judge sözleşmesi:
`Callable[[list[tuple[StepKind, str]]], bool]`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal

Judge = Callable[[list[tuple[StepKind, str]]], bool]


def make_judge(goal: Goal, sandbox: Path, last_exit: dict[str, int]) -> Judge:
    """Goal.judge_kind'a göre uygun judge closure'u üretir."""
    kind = goal.judge_kind
    arg = goal.judge_arg

    if kind == "file_exists":
        target = sandbox / arg

        def _file_exists(_history: list[tuple[StepKind, str]]) -> bool:
            return target.is_file()

        return _file_exists

    if kind == "regex_in_last_observe":
        try:
            pat = re.compile(arg)
        except re.error as exc:
            raise ValueError(f"judge_arg regex derlenemedi: {exc}") from exc

        def _regex(history: list[tuple[StepKind, str]]) -> bool:
            for kind_, text in reversed(history):
                if kind_ is StepKind.OBSERVE:
                    return bool(pat.search(text))
            return False

        return _regex

    if kind == "exit_zero":
        def _exit_zero(_history: list[tuple[StepKind, str]]) -> bool:
            return last_exit.get("shell") == 0

        return _exit_zero

    raise ValueError(f"bilinmeyen judge_kind: {kind}")

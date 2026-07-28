"""Planner fabrikaları — static (deterministik) + llm (stub).

SPEC 002 §3 (FR2). `run_loop`'un beklediği plan sözleşmesi:
`Callable[[goal: str, history: list[tuple[StepKind, str]]], str]`.

Gerçek LLM entegrasyonu (`claude` subprocess) bu görev DIŞI —
Görev 003'te eklenecek.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal

Planner = Callable[[str, list[tuple[StepKind, str]]], str]


class PlannerExhaustedError(RuntimeError):
    """Static plan listesi tükendi ama hedef sağlanmadı."""


def make_planner(goal: Goal) -> Planner:
    """Goal.plan_kind'a göre uygun planner closure'u üretir.

    - `static`: plan_steps'i sırayla döndürür; tükenirse
      `PlannerExhaustedError`.
    - `llm` + `ATLAS_LLM=stub` (varsayılan): sabit `noop` +
      `plan[stub]:` prefix'i.
    - `llm` + başka backend: `NotImplementedError` (Görev 003).
    """
    if goal.plan_kind == "static":
        steps = list(goal.plan_steps)
        idx = {"i": 0}

        def _static(_goal: str, _history: list[tuple[StepKind, str]]) -> str:
            if idx["i"] >= len(steps):
                raise PlannerExhaustedError(f"plan_steps tukendi ({len(steps)} adim)")
            step = steps[idx["i"]]
            idx["i"] += 1
            return step

        return _static

    if goal.plan_kind == "llm":
        backend = os.environ.get("ATLAS_LLM", "stub")
        if backend == "stub":
            def _stub(_goal: str, _history: list[tuple[StepKind, str]]) -> str:
                return "plan[stub]:noop"

            return _stub
        raise NotImplementedError(f"LLM backend '{backend}' Görev 003'te eklenecek")

    raise ValueError(f"bilinmeyen plan_kind: {goal.plan_kind}")

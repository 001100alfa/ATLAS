"""SPEC 002 §3 (FR2) — Planner testleri (Adım 3.3)."""

from __future__ import annotations

import pytest

from atlas_core.orchestrator.goals import Goal
from atlas_core.orchestrator.planner import PlannerExhaustedError, make_planner


def _goal(kind: str, steps: tuple[str, ...] = ()) -> Goal:
    return Goal(
        goal="t",
        plan_kind=kind,  # type: ignore[arg-type]
        plan_steps=steps,
        action_allowlist=frozenset({"read"}),
        shell_allow_regex=None,
        judge_kind="file_exists",
        judge_arg="x",
        budget=10.0,
        max_steps=5,
        costs={"read": 1.0, "write": 2.0, "shell": 5.0},
    )


def test_static_sirayla_dondurur() -> None:
    p = make_planner(_goal("static", ("a", "b", "c")))
    assert p("g", []) == "a"
    assert p("g", []) == "b"
    assert p("g", []) == "c"


def test_static_tukenince_hata() -> None:
    p = make_planner(_goal("static", ("tek",)))
    p("g", [])
    with pytest.raises(PlannerExhaustedError, match="tukendi"):
        p("g", [])


def test_llm_stub_deterministik(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_LLM", raising=False)
    p = make_planner(_goal("llm"))
    assert p("g", []) == "plan[stub]:noop"
    assert p("g", [("plan", "x")]) == "plan[stub]:noop"


def test_llm_bilinmeyen_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    # SPEC 003 + 003.1: claude, anthropic, acp artık desteklenen backend'ler.
    monkeypatch.setenv("ATLAS_LLM", "xyz")
    with pytest.raises(NotImplementedError) as exc_info:
        make_planner(_goal("llm"))
    msg = str(exc_info.value)
    # Mesaj bilinmeyen adı + tüm desteklenen backend'leri içermeli.
    assert "xyz" in msg
    for backend in ("stub", "claude", "anthropic", "acp"):
        assert backend in msg, f"'{backend}' desteklenen listede görünmeli"

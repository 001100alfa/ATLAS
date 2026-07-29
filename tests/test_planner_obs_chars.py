"""SPEC 018 — Gözlem uzunluk kırpma env testleri."""

from __future__ import annotations

import pytest

from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal
from atlas_core.orchestrator.planner import _format_prompt, _read_obs_chars_env


def _goal() -> Goal:
    return Goal(
        goal="dosya yaz",
        plan_kind="llm",
        plan_steps=(),
        action_allowlist=frozenset({"write"}),
        shell_allow_regex=None,
        judge_kind="file_exists",
        judge_arg="out.txt",
        budget=20.0,
        max_steps=3,
        costs={"read": 1.0, "write": 2.0, "shell": 5.0},
    )


def test_018_env_yok_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_LLM_OBS_CHARS", raising=False)
    assert _read_obs_chars_env() == 200


def test_018_env_gecerli_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "500")
    assert _read_obs_chars_env() == 500


def test_018_env_parse_hata_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "abc")
    assert _read_obs_chars_env() == 200


def test_018_env_negatif_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "-1")
    assert _read_obs_chars_env() == 200


def test_018_env_sifir_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "0")
    assert _read_obs_chars_env() == 200


def test_018_env_ustsinir_asim_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "5000")
    assert _read_obs_chars_env() == 200


def test_018_env_ustsinirda_kabul(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "2000")
    assert _read_obs_chars_env() == 2000


def _base_x_count(monkeypatch: pytest.MonkeyPatch) -> int:
    """Prompt şablonunda sabit x sayısı (örn. 'notes.txt' içindeki)."""
    base = _format_prompt(_goal(), [])
    return base.count("x")


def test_018_format_prompt_varsayilan_200(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env yok → gözlem 200 karakterde kırpılır (bit-uyumlu)."""
    monkeypatch.delenv("ATLAS_LLM_OBS_CHARS", raising=False)
    base = _base_x_count(monkeypatch)
    long_obs = "x" * 500
    history = [(StepKind.OBSERVE, long_obs)]
    prompt = _format_prompt(_goal(), history)
    x_count = prompt.count("x")
    assert x_count == base + 200


def test_018_format_prompt_env_ile_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = _base_x_count(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "500")
    long_obs = "x" * 1000
    history = [(StepKind.OBSERVE, long_obs)]
    prompt = _format_prompt(_goal(), history)
    x_count = prompt.count("x")
    assert x_count == base + 500

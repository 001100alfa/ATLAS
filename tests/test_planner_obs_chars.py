"""SPEC 018 — Gözlem uzunluk kırpma env testleri."""

from __future__ import annotations

import pytest

from atlas_core.orchestrator import planner as planner_mod
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
    """SPEC 018 + 018.1: obs_chars=500, head+tail 100+100 varsayılan.

    Uzun obs → head+tail 200 x + arada `[... N char atlandı ...]` işareti.
    """
    base = _base_x_count(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "500")
    monkeypatch.delenv("ATLAS_LLM_OBS_HEAD", raising=False)
    monkeypatch.delenv("ATLAS_LLM_OBS_TAIL", raising=False)
    long_obs = "x" * 1000
    history = [(StepKind.OBSERVE, long_obs)]
    prompt = _format_prompt(_goal(), history)
    x_count = prompt.count("x")
    # head=100 + tail=100 = 200 x
    assert x_count == base + 200
    assert "atlandı" in prompt


# ---------- SPEC 018.1: head+tail keep ----------


def test_018_1_env_okuma_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_LLM_OBS_HEAD", raising=False)
    monkeypatch.delenv("ATLAS_LLM_OBS_TAIL", raising=False)
    assert planner_mod._read_obs_head_tail_env() == (100, 100)


def test_018_1_env_okuma_ozel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_HEAD", "50")
    monkeypatch.setenv("ATLAS_LLM_OBS_TAIL", "30")
    assert planner_mod._read_obs_head_tail_env() == (50, 30)


def test_018_1_env_parse_hata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_HEAD", "abc")
    monkeypatch.setenv("ATLAS_LLM_OBS_TAIL", "xyz")
    assert planner_mod._read_obs_head_tail_env() == (100, 100)


def test_018_1_env_negatif_sifira(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_OBS_HEAD", "-10")
    monkeypatch.setenv("ATLAS_LLM_OBS_TAIL", "-5")
    assert planner_mod._read_obs_head_tail_env() == (0, 0)


def test_018_1_trim_kisa_obs_dokunulmaz(monkeypatch: pytest.MonkeyPatch) -> None:
    """`len(obs) <= obs_chars` → dokunulmaz."""
    monkeypatch.delenv("ATLAS_LLM_OBS_HEAD", raising=False)
    monkeypatch.delenv("ATLAS_LLM_OBS_TAIL", raising=False)
    assert planner_mod._trim_obs("kısa", 100) == "kısa"


def test_018_1_trim_head_tail_bolunur(monkeypatch: pytest.MonkeyPatch) -> None:
    """Uzun obs → head + [... N char atlandı ...] + tail."""
    monkeypatch.setenv("ATLAS_LLM_OBS_HEAD", "5")
    monkeypatch.setenv("ATLAS_LLM_OBS_TAIL", "5")
    obs = "A" * 10 + "middle" + "Z" * 10  # 26 char
    result = planner_mod._trim_obs(obs, obs_chars=20)  # 5+5 < 20
    assert result.startswith("A" * 5)
    assert result.endswith("Z" * 5)
    assert "atlandı" in result
    assert "middle" not in result


def test_018_1_trim_head_tail_sifir_018_davranisi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """head+tail=0 → 018 davranışı (`obs[:obs_chars]`)."""
    monkeypatch.setenv("ATLAS_LLM_OBS_HEAD", "0")
    monkeypatch.setenv("ATLAS_LLM_OBS_TAIL", "0")
    obs = "x" * 500
    result = planner_mod._trim_obs(obs, obs_chars=200)
    assert result == "x" * 200
    assert "atlandı" not in result


def test_018_1_mantiksiz_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """head+tail >= obs_chars → 018 davranışı fallback."""
    monkeypatch.setenv("ATLAS_LLM_OBS_HEAD", "500")
    monkeypatch.setenv("ATLAS_LLM_OBS_TAIL", "500")
    obs = "x" * 5000
    result = planner_mod._trim_obs(obs, obs_chars=200)
    # 500+500=1000 > 200 → 018 fallback
    assert result == "x" * 200

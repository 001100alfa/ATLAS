"""SPEC 018.2 — LLM ile gerçek gözlem özetleme testleri."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from atlas_core.orchestrator import planner as planner_mod
from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal, load_goal
from atlas_core.orchestrator.planner import (
    LLMPlannerError,
    _effective_obs_summarize,
    _format_prompt,
    _maybe_summarize_or_trim,
    _read_env_flag,
    _reset_obs_summarize_warnings,
    _stub_summarize_obs,
)


def _goal(*, obs_summarize: bool = False) -> Goal:
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
        obs_summarize=obs_summarize,
    )


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Her testte uyarı seti + env sıfırla."""
    _reset_obs_summarize_warnings()
    monkeypatch.delenv("ATLAS_LLM_OBS_SUMMARIZE", raising=False)
    monkeypatch.delenv("ATLAS_LLM", raising=False)
    monkeypatch.delenv("ATLAS_LLM_OBS_CHARS", raising=False)


# ─────────────────────────────────────────────────────────────────────
# Env flag + effective
# ─────────────────────────────────────────────────────────────────────


def test_0182_env_flag_truthy(monkeypatch: pytest.MonkeyPatch) -> None:
    """1/true/yes/on truthy, diğerleri değil."""
    for val in ("1", "true", "YES", "On", "TRUE"):
        monkeypatch.setenv("ATLAS_LLM_OBS_SUMMARIZE", val)
        assert _read_env_flag("ATLAS_LLM_OBS_SUMMARIZE"), val
    for val in ("0", "false", "no", "off", "", "maybe"):
        monkeypatch.setenv("ATLAS_LLM_OBS_SUMMARIZE", val)
        assert not _read_env_flag("ATLAS_LLM_OBS_SUMMARIZE"), val


def test_0182_effective_goal_veya_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Effective flag: goal.obs_summarize VEYA env."""
    assert not _effective_obs_summarize(_goal())
    assert _effective_obs_summarize(_goal(obs_summarize=True))
    monkeypatch.setenv("ATLAS_LLM_OBS_SUMMARIZE", "1")
    assert _effective_obs_summarize(_goal())  # env override


# ─────────────────────────────────────────────────────────────────────
# Stub summarizer (deterministik)
# ─────────────────────────────────────────────────────────────────────


def test_0182_stub_summarizer_deterministik() -> None:
    """Aynı input → aynı output."""
    obs = "hata: dosya bulunamadı\nsatır 2\nsatır 3"
    a = _stub_summarize_obs(obs)
    b = _stub_summarize_obs(obs)
    assert a == b
    assert a.startswith("[özet: ")
    assert "char" in a
    assert "satır" in a


def test_0182_stub_summarizer_bos_string() -> None:
    """Boş string patlamamalı."""
    out = _stub_summarize_obs("")
    assert out.startswith("[özet: 0 char")


# ─────────────────────────────────────────────────────────────────────
# Dispatch: maybe_summarize_or_trim
# ─────────────────────────────────────────────────────────────────────


def test_0182_kisa_obs_dokunma(monkeypatch: pytest.MonkeyPatch) -> None:
    """`len(obs) <= obs_chars` → summarizer ÇAĞRILMAZ, obs birebir döner."""
    monkeypatch.setenv("ATLAS_LLM_OBS_SUMMARIZE", "1")
    monkeypatch.setenv("ATLAS_LLM", "anthropic")  # bile anthropic olsa
    obs = "kısa çıktı"
    # obs_chars=200 varsayılan; 10 char < 200
    out = _maybe_summarize_or_trim(obs, 200, _goal(obs_summarize=True))
    assert out == obs  # dokunulmadı, ekstra maliyet yok


def test_0182_kapali_ise_trim_davranisi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opt-in kapalı → 018.1 kırpma davranışı (özet YOK)."""
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    long_obs = "x" * 500
    out = _maybe_summarize_or_trim(long_obs, 100, _goal())  # obs_summarize=False
    assert "[özet:" not in out
    # 018.1 default head=100+tail=100=200 >= 100 → 018 kırpma → obs[:100]
    assert out == "x" * 100


def test_0182_stub_backend_stub_ozet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Backend stub + opt-in aktif → deterministik stub özet."""
    monkeypatch.setenv("ATLAS_LLM", "stub")
    long_obs = "hata satırı\n" * 100
    out = _maybe_summarize_or_trim(long_obs, 50, _goal(obs_summarize=True))
    assert out.startswith("[özet: ")
    assert "char" in out


def test_0182_claude_uyarisi_bir_kez(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Backend claude + opt-in → uyarı bir kez basılır, sonra stub'a düşer."""
    monkeypatch.setenv("ATLAS_LLM", "claude")
    long_obs = "x" * 500
    g = _goal(obs_summarize=True)
    _ = _maybe_summarize_or_trim(long_obs, 100, g)
    _ = _maybe_summarize_or_trim(long_obs, 100, g)
    _ = _maybe_summarize_or_trim(long_obs, 100, g)
    err = capsys.readouterr().err
    # Sadece bir kez uyarı
    assert err.count("uyarı: obs_summarize 'claude'") == 1


def test_0182_acp_uyarisi_bir_kez(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Backend acp + opt-in → uyarı bir kez, stub'a düşer."""
    monkeypatch.setenv("ATLAS_LLM", "acp")
    long_obs = "x" * 500
    g = _goal(obs_summarize=True)
    _ = _maybe_summarize_or_trim(long_obs, 100, g)
    _ = _maybe_summarize_or_trim(long_obs, 100, g)
    err = capsys.readouterr().err
    assert "uyarı: obs_summarize 'acp'" in err
    assert err.count("uyarı: obs_summarize 'acp'") == 1


# ─────────────────────────────────────────────────────────────────────
# Anthropic real çağrı (mock ile)
# ─────────────────────────────────────────────────────────────────────


def test_0182_anthropic_real_call_ozet_doner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backend anthropic + opt-in → _call_anthropic çağrılır, özet döner."""
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-xxx")

    calls: list[dict[str, Any]] = []

    def fake_call(**kwargs: Any) -> str:
        calls.append(kwargs)
        return "Kısa özet: dosya izinsiz"

    monkeypatch.setattr(planner_mod, "_call_anthropic", fake_call)

    long_obs = "hata: izin yok\n" + "x" * 500
    out = _maybe_summarize_or_trim(long_obs, 100, _goal(obs_summarize=True))
    assert out == "[özet: Kısa özet: dosya izinsiz]"
    # _call_anthropic tam bir kez çağrıldı
    assert len(calls) == 1
    # Prompt'ta gözlemin kırpılmış hali (max 2000 char) var
    assert "Aşağıdaki komut çıktısını Türkçe" in calls[0]["prompt"]
    assert "hata: izin yok" in calls[0]["prompt"]


def test_0182_anthropic_hata_fallback_trim(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Anthropic LLMPlannerError → uyarı stderr + _trim_obs fallback."""
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-xxx")

    def fake_call(**_kwargs: Any) -> str:
        raise LLMPlannerError("anthropic HTTP 500: sunucu hatası")

    monkeypatch.setattr(planner_mod, "_call_anthropic", fake_call)

    long_obs = "x" * 500
    out = _maybe_summarize_or_trim(long_obs, 100, _goal(obs_summarize=True))
    # Fallback: 018.1 kırpma davranışı (özet formatı YOK)
    assert not out.startswith("[özet:")
    err = capsys.readouterr().err
    assert "obs_summarize anthropic çağrısı başarısız" in err
    assert "HTTP 500" in err


def test_0182_anthropic_uzun_ozet_kirpilir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Özet 120 char'dan uzunsa kırpılır + `…` eklenir."""
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-xxx")

    long_summary = "A" * 200
    monkeypatch.setattr(
        planner_mod, "_call_anthropic",
        lambda **_k: long_summary,
    )

    out = _maybe_summarize_or_trim("x" * 500, 100, _goal(obs_summarize=True))
    # "[özet: " + 119 char + "…" + "]"  → toplam 120 + wrapping
    assert out.endswith("…]")
    inner = out[len("[özet: "):-1]  # trailing ]
    assert len(inner) == 120


# ─────────────────────────────────────────────────────────────────────
# _format_prompt entegrasyonu
# ─────────────────────────────────────────────────────────────────────


def test_0182_format_prompt_stub_ozet_gorunur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_format_prompt uzun obs varsa stub özeti prompt'a gömer (stub backend)."""
    monkeypatch.setenv("ATLAS_LLM", "stub")
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "50")
    history = [(StepKind.OBSERVE, "y" * 500)]
    prompt = _format_prompt(_goal(obs_summarize=True), history)
    assert "[özet: 500 char" in prompt


def test_0182_format_prompt_kapali_trim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """obs_summarize kapalı → prompt'ta özet formatı YOK, 018 kırpması var."""
    monkeypatch.setenv("ATLAS_LLM", "stub")
    monkeypatch.setenv("ATLAS_LLM_OBS_CHARS", "50")
    history = [(StepKind.OBSERVE, "y" * 500)]
    prompt = _format_prompt(_goal(), history)  # obs_summarize=False
    assert "[özet:" not in prompt


# ─────────────────────────────────────────────────────────────────────
# YAML yükleme (goals.py)
# ─────────────────────────────────────────────────────────────────────


def test_0182_yaml_obs_summarize_yuklenir(tmp_path: Path) -> None:
    """YAML `obs_summarize: true` alanı `Goal`'a yansır."""
    y = tmp_path / "g.yaml"
    y.write_text(
        "goal: özet dene\nplan_kind: llm\nplan_steps: []\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: x.txt\nbudget: 20\nmax_steps: 2\n"
        "obs_summarize: true\n",
        encoding="utf-8",
    )
    g = load_goal(y)
    assert g.obs_summarize is True


def test_0182_yaml_obs_summarize_varsayilan_false(tmp_path: Path) -> None:
    """YAML alanı yoksa `obs_summarize=False` (bit-uyumlu)."""
    y = tmp_path / "g.yaml"
    y.write_text(
        "goal: özet dene\nplan_kind: llm\nplan_steps: []\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: x.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    g = load_goal(y)
    assert g.obs_summarize is False


def test_0182_yaml_obs_summarize_bool_degil_hata(tmp_path: Path) -> None:
    """YAML alanı bool değilse SpecError."""
    from atlas_core.orchestrator.goals import SpecError

    y = tmp_path / "g.yaml"
    y.write_text(
        "goal: özet dene\nplan_kind: llm\nplan_steps: []\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: x.txt\nbudget: 20\nmax_steps: 2\n"
        "obs_summarize: yes-string\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="obs_summarize bool olmalı"):
        load_goal(y)

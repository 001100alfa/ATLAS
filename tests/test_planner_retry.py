"""SPEC 008 — LLM retry/backoff sarmalayıcı testleri."""

from __future__ import annotations

from typing import Any

import pytest

from atlas_core.orchestrator import planner as planner_mod
from atlas_core.orchestrator.planner import (
    LLMPlannerError,
    PlannerExhaustedError,
    _read_retry_env,
    make_retrying_planner,
)

# ---------- Yardımcılar ----------

class _CountingPlanner:
    """Script'lenmiş cevap sırası; her çağrıda bir sonraki elemanı verir.

    Element str → döner; Element Exception → raise.
    """

    def __init__(self, script: list[Any]) -> None:
        self.script = list(script)
        self.calls = 0

    def __call__(self, goal: str, history: list[Any]) -> str:
        i = self.calls
        self.calls += 1
        item = self.script[min(i, len(self.script) - 1)]
        # KeyboardInterrupt/SystemExit BaseException'dan türer — Exception değil.
        if isinstance(item, BaseException):
            raise item
        return str(item)


# ---------- AC1: retries=0 kimlik ----------

def test_ac1_retries_sifir_kimlik() -> None:
    inner = _CountingPlanner(["ok"])
    assert make_retrying_planner(inner, 0, 1.0) is inner
    # Aynı davranış: tek çağrı ok döner
    assert inner("g", []) == "ok"


def test_ac1_retries_negatif_kimlik() -> None:
    inner = _CountingPlanner(["ok"])
    assert make_retrying_planner(inner, -3, 1.0) is inner


# ---------- AC2: 2. denemede başarı ----------

def test_ac2_ikinci_denemede_basari(monkeypatch: pytest.MonkeyPatch) -> None:
    inner = _CountingPlanner([LLMPlannerError("timeout"), "write:x"])
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    p = make_retrying_planner(inner, retries=1, backoff_s=1.0)
    assert p("g", []) == "write:x"
    assert inner.calls == 2


# ---------- AC3: tüm denemeler başarısız ----------

def test_ac3_tum_denemeler_basarisiz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Son yakalanan istisna raise edilir, mesajı son deneminindir."""
    inner = _CountingPlanner([
        LLMPlannerError("first"),
        LLMPlannerError("second"),
        LLMPlannerError("third"),
        LLMPlannerError("fourth"),
    ])
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    p = make_retrying_planner(inner, retries=3, backoff_s=1.0)
    with pytest.raises(LLMPlannerError) as exc_info:
        p("g", [])
    assert "fourth" in str(exc_info.value)
    assert inner.calls == 4


# ---------- AC4: geometrik backoff ----------

def test_ac4_geometrik_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    inner = _CountingPlanner([LLMPlannerError("x")] * 4)
    p = make_retrying_planner(inner, retries=3, backoff_s=1.0)
    with pytest.raises(LLMPlannerError):
        p("g", [])
    assert sleeps == [1.0, 2.0, 4.0]


def test_ac4_backoff_taban_yarim(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    inner = _CountingPlanner([LLMPlannerError("x")] * 3)
    p = make_retrying_planner(inner, retries=2, backoff_s=0.5)
    with pytest.raises(LLMPlannerError):
        p("g", [])
    assert sleeps == [0.5, 1.0]


# ---------- AC5: backoff=0 sleep atlanmaz (gerçek 0s bekle) ----------

def test_ac5_backoff_sifir_sleep_cagrilir_ama_sifir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """backoff=0 → sleep çağrılır ama 0s ile (test hızını bozmaz)."""
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    inner = _CountingPlanner([LLMPlannerError("x"), LLMPlannerError("y"), "ok"])
    p = make_retrying_planner(inner, retries=2, backoff_s=0.0)
    assert p("g", []) == "ok"
    assert sleeps == [0.0, 0.0]


# ---------- AC6: PlannerExhausted geçer ----------

def test_ac6_planner_exhausted_gecer(monkeypatch: pytest.MonkeyPatch) -> None:
    inner = _CountingPlanner([PlannerExhaustedError("tükendi")])
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    p = make_retrying_planner(inner, retries=3, backoff_s=1.0)
    with pytest.raises(PlannerExhaustedError):
        p("g", [])
    assert inner.calls == 1  # retry yok


# ---------- AC7: KeyboardInterrupt geçer ----------

def test_ac7_keyboard_interrupt_gecer(monkeypatch: pytest.MonkeyPatch) -> None:
    inner = _CountingPlanner([KeyboardInterrupt()])
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    p = make_retrying_planner(inner, retries=3, backoff_s=1.0)
    with pytest.raises(KeyboardInterrupt):
        p("g", [])
    assert inner.calls == 1


def test_ac7_diger_istisna_gecer(monkeypatch: pytest.MonkeyPatch) -> None:
    inner = _CountingPlanner([ValueError("başka")])
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    p = make_retrying_planner(inner, retries=3, backoff_s=1.0)
    with pytest.raises(ValueError):
        p("g", [])
    assert inner.calls == 1


# ---------- AC8: trace stderr açık ----------

def test_ac8_trace_stderr_acik(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ATLAS_LLM_TRACE", "1")
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    inner = _CountingPlanner([
        LLMPlannerError("first"),
        LLMPlannerError("second"),
        LLMPlannerError("third"),
    ])
    p = make_retrying_planner(inner, retries=2, backoff_s=1.0)
    with pytest.raises(LLMPlannerError):
        p("g", [])
    err = capsys.readouterr().err
    assert "[retry] deneme 1/3 başarısız" in err
    assert "[retry] deneme 2/3 başarısız" in err
    assert "[retry] deneme 3/3 başarısız" in err
    assert "first" in err and "second" in err and "third" in err


# ---------- AC9: trace kapalı ----------

def test_ac9_trace_kapali_stderr_temiz(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("ATLAS_LLM_TRACE", raising=False)
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    inner = _CountingPlanner([LLMPlannerError("x"), "ok"])
    p = make_retrying_planner(inner, retries=1, backoff_s=1.0)
    p("g", [])
    assert "[retry]" not in capsys.readouterr().err


# ---------- AC10: env okuma ----------

def test_ac10_env_okuma_varsayilanlar(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_LLM_RETRIES", raising=False)
    monkeypatch.delenv("ATLAS_LLM_BACKOFF", raising=False)
    assert _read_retry_env() == (0, 1.0)


def test_ac10_env_negatif_sifira_dusurulur(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_RETRIES", "-5")
    monkeypatch.setenv("ATLAS_LLM_BACKOFF", "-1.5")
    assert _read_retry_env() == (0, 0.0)


def test_ac10_env_normal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_RETRIES", "3")
    monkeypatch.setenv("ATLAS_LLM_BACKOFF", "0.25")
    assert _read_retry_env() == (3, 0.25)

"""SPEC 008 — LLM retry/backoff sarmalayıcı testleri."""

from __future__ import annotations

from typing import Any

import pytest

from atlas_core.orchestrator import planner as planner_mod
from atlas_core.orchestrator.planner import (
    LLMPlannerError,
    PlannerExhaustedError,
    RetryAfterError,
    _read_jitter_env,
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


# ---------- SPEC 014: jitter + RetryAfter ----------


def test_014_jitter_env_okuma(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_LLM_JITTER", raising=False)
    assert _read_jitter_env() == 0.0
    monkeypatch.setenv("ATLAS_LLM_JITTER", "0.5")
    assert _read_jitter_env() == 0.5
    monkeypatch.setenv("ATLAS_LLM_JITTER", "-1")
    assert _read_jitter_env() == 0.0
    monkeypatch.setenv("ATLAS_LLM_JITTER", "abc")
    assert _read_jitter_env() == 0.0


def test_014_jitter_backoff_ustune_eklenir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM_JITTER", "0.5")
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    # random deterministik
    monkeypatch.setattr(planner_mod.random, "uniform", lambda _a, _b: 0.3)

    inner = _CountingPlanner([LLMPlannerError("x"), LLMPlannerError("y"), "ok"])
    p = make_retrying_planner(inner, retries=2, backoff_s=1.0)
    assert p("g", []) == "ok"
    # backoff sırası: 1.0 + 0.3, 2.0 + 0.3
    assert sleeps == pytest.approx([1.3, 2.3])


def test_014_jitter_kapali_backoff_deterministik(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Jitter 0 → 008 davranışı bit-uyumlu."""
    monkeypatch.delenv("ATLAS_LLM_JITTER", raising=False)
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    # random hiç çağrılmamalı
    called = {"n": 0}

    def spy_uniform(_a: float, _b: float) -> float:
        called["n"] += 1
        return 999.0

    monkeypatch.setattr(planner_mod.random, "uniform", spy_uniform)
    inner = _CountingPlanner([LLMPlannerError("x")] * 4)
    p = make_retrying_planner(inner, retries=3, backoff_s=1.0)
    with pytest.raises(LLMPlannerError):
        p("g", [])
    assert sleeps == [1.0, 2.0, 4.0]
    assert called["n"] == 0  # jitter kapalı → random.uniform çağrılmadı


def test_014_retry_after_error_backoff_yerine_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RetryAfterError yakalanırsa bekleme header saniyesi (backoff değil)."""
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    inner = _CountingPlanner([
        RetryAfterError("throttle", retry_after_s=7.5),
        "ok",
    ])
    p = make_retrying_planner(inner, retries=1, backoff_s=100.0)  # backoff büyük
    assert p("g", []) == "ok"
    assert sleeps == [7.5]  # header saniyesi kullanıldı


def test_014_retry_after_jitter_yok_sayilir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Header verildiyse jitter eklenmez — sunucu ipucu tam saygı."""
    monkeypatch.setenv("ATLAS_LLM_JITTER", "10.0")
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    inner = _CountingPlanner([
        RetryAfterError("throttle", retry_after_s=3.0),
        "ok",
    ])
    p = make_retrying_planner(inner, retries=1, backoff_s=1.0)
    p("g", [])
    assert sleeps == [3.0]  # jitter eklenmedi


def test_014_retry_after_karisik(monkeypatch: pytest.MonkeyPatch) -> None:
    """İlk deneme RetryAfter → header; ikinci sıradan → backoff."""
    sleeps: list[float] = []
    monkeypatch.setattr(planner_mod, "_sleep", lambda s: sleeps.append(s))
    monkeypatch.delenv("ATLAS_LLM_JITTER", raising=False)
    inner = _CountingPlanner([
        RetryAfterError("throttle", retry_after_s=5.0),
        LLMPlannerError("normal"),
        LLMPlannerError("normal"),
    ])
    p = make_retrying_planner(inner, retries=2, backoff_s=1.0)
    with pytest.raises(LLMPlannerError):
        p("g", [])
    # 1. attempt (RetryAfter): 5.0
    # 2. attempt (normal): 1.0 * 2**1 = 2.0
    assert sleeps == [5.0, 2.0]

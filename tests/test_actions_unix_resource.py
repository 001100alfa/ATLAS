"""SPEC 026.1 — Unix `resource` limitleri testleri.

Unix-canlı testler: RLIMIT_CPU + RLIMIT_AS gerçek subprocess ile
doğrulanır (`skipif Windows`).
Windows-canlı test: env verilse de preexec_fn None (bit-uyumlu 026).
Ortak: `_read_positive_int_env` + `_build_preexec_fn` platform-agnostik.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from atlas_core.orchestrator import actions as actions_mod
from atlas_core.orchestrator.actions import (
    _build_preexec_fn,
    _read_positive_int_env,
    make_action,
)
from atlas_core.orchestrator.goals import Goal


def _goal_shell() -> Goal:
    return Goal(
        goal="cpu/mem sınır dene",
        plan_kind="static",
        plan_steps=(),
        action_allowlist=frozenset({"shell"}),
        shell_allow_regex=re.compile(r".*"),
        judge_kind="exit_zero",
        judge_arg="",
        budget=100.0,
        max_steps=3,
        costs={"read": 1.0, "write": 2.0, "shell": 5.0},
    )


# ─────────────────────────────────────────────────────────────────────
# Env parse — platform-agnostik
# ─────────────────────────────────────────────────────────────────────


def test_0261_env_yok_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_SANDBOX_CPU_S", raising=False)
    assert _read_positive_int_env("ATLAS_SANDBOX_CPU_S") is None


def test_0261_env_gecerli_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "5")
    assert _read_positive_int_env("ATLAS_SANDBOX_CPU_S") == 5


def test_0261_env_parse_hata_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "abc")
    assert _read_positive_int_env("ATLAS_SANDBOX_CPU_S") is None


def test_0261_env_sifir_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "0")
    assert _read_positive_int_env("ATLAS_SANDBOX_CPU_S") is None


def test_0261_env_negatif_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "-1")
    assert _read_positive_int_env("ATLAS_SANDBOX_CPU_S") is None


def test_0261_env_bos_string_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "   ")
    assert _read_positive_int_env("ATLAS_SANDBOX_CPU_S") is None


# ─────────────────────────────────────────────────────────────────────
# _build_preexec_fn — Windows: her zaman None
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only guard testi")
def test_0261_windows_env_verili_yine_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows'ta env verilse de preexec_fn None — subprocess ValueError'dan korunur."""
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "1")
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "32")
    assert _build_preexec_fn() is None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only guard testi")
def test_0261_windows_shell_calisir_env_verili(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Windows: env verilse de shell normal çalışır (kısıt yok, no-op)."""
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "1")
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "32")
    action = make_action(_goal_shell(), tmp_path)
    obs, cost = action("shell:cmd /c echo ok")
    assert "exit=0" in obs
    assert "ok" in obs


# ─────────────────────────────────────────────────────────────────────
# _build_preexec_fn — Unix: env yok → None (bit-uyumlu)
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
def test_0261_unix_env_yok_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_SANDBOX_CPU_S", raising=False)
    monkeypatch.delenv("ATLAS_SANDBOX_MEM_MB", raising=False)
    assert _build_preexec_fn() is None


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
def test_0261_unix_cpu_verili_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "5")
    monkeypatch.delenv("ATLAS_SANDBOX_MEM_MB", raising=False)
    fn = _build_preexec_fn()
    assert callable(fn)


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
def test_0261_unix_mem_verili_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_SANDBOX_CPU_S", raising=False)
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "32")
    fn = _build_preexec_fn()
    assert callable(fn)


# ─────────────────────────────────────────────────────────────────────
# Unix canlı — CPU + MEM limit gerçek subprocess
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only canlı test")
def test_0261_unix_cpu_limit_sigxcpu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CPU_S=1 iken sonsuz döngü SIGXCPU/SIGKILL ile 3 sn'den kısa kesilir."""
    import time

    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "1")
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "8.0")  # timeout > cpu_s
    action = make_action(_goal_shell(), tmp_path)
    t0 = time.monotonic()
    obs, _ = action('shell:python3 -c "while True: pass"')
    elapsed = time.monotonic() - t0
    # SIGXCPU (24) veya SIGKILL sonrası exit negatif ya da 137
    assert "exit=" in obs
    exit_str = obs.split("exit=")[1].split()[0]
    exit_code = int(exit_str)
    assert exit_code != 0  # ölmüş
    # 3 sn'den kısa: CPU limit çalışıyor, timeout değil
    assert elapsed < 3.5, f"CPU limit calışmadı, {elapsed:.1f}s sürdü"


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only canlı test")
def test_0261_unix_mem_limit_memerror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MEM_MB=32 iken 200MB allocation MemoryError → exit != 0."""
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "64")
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "8.0")
    action = make_action(_goal_shell(), tmp_path)
    obs, _ = action(
        'shell:python3 -c "x = bytearray(500 * 1024 * 1024); print(len(x))"'
    )
    assert "exit=" in obs
    exit_str = obs.split("exit=")[1].split()[0]
    exit_code = int(exit_str)
    assert exit_code != 0  # MemoryError veya SIGKILL


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
def test_0261_unix_env_yok_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Env yoksa shell normal çalışır, 026 davranışıyla eş."""
    monkeypatch.delenv("ATLAS_SANDBOX_CPU_S", raising=False)
    monkeypatch.delenv("ATLAS_SANDBOX_MEM_MB", raising=False)
    action = make_action(_goal_shell(), tmp_path)
    obs, _ = action("shell:echo bit-uyumlu")
    assert "exit=0" in obs
    assert "bit-uyumlu" in obs


# ─────────────────────────────────────────────────────────────────────
# Resource modülü mocked (Windows dahil kod yolu kapsamı)
# ─────────────────────────────────────────────────────────────────────


def test_0261_resource_yok_gibi_davran(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_resource is None` → env verilse de preexec_fn None (import guard)."""
    monkeypatch.setattr(actions_mod, "_resource", None)
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "5")
    # sys.platform Windows olmasa bile _resource None ise None dönmeli
    assert _build_preexec_fn() is None


# ═════════════════════════════════════════════════════════════════════
# SPEC 026.4 — Unix MAX_PROC (RLIMIT_NPROC)
# ═════════════════════════════════════════════════════════════════════


def test_0264_env_max_proc_yalniz_none_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows'ta MAX_PROC verilse de _build_preexec_fn None döner."""
    if sys.platform != "win32":
        pytest.skip("Windows-only guard")
    monkeypatch.setenv("ATLAS_SANDBOX_MAX_PROC", "5")
    assert _build_preexec_fn() is None


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
def test_0264_unix_max_proc_verili_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unix'te MAX_PROC verildiyse _build_preexec_fn callable döner."""
    monkeypatch.delenv("ATLAS_SANDBOX_CPU_S", raising=False)
    monkeypatch.delenv("ATLAS_SANDBOX_MEM_MB", raising=False)
    monkeypatch.setenv("ATLAS_SANDBOX_MAX_PROC", "10")
    fn = _build_preexec_fn()
    assert callable(fn)


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
def test_0264_unix_rlimit_nproc_yok_sessiz(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_resource.RLIMIT_NPROC` platformda yoksa yine callable (getattr None)."""
    import types

    fake_resource = types.SimpleNamespace(
        RLIMIT_CPU=0,
        RLIMIT_AS=9,
        setrlimit=lambda *_a: None,
        # RLIMIT_NPROC KASITEN yok
    )
    monkeypatch.setattr(actions_mod, "_resource", fake_resource)
    monkeypatch.setenv("ATLAS_SANDBOX_MAX_PROC", "5")
    fn = _build_preexec_fn()
    assert callable(fn)
    # Çağrı da patlamamalı (RLIMIT_NPROC atlanır)
    fn()


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
def test_0264_unix_setrlimit_mock_cagirir(monkeypatch: pytest.MonkeyPatch) -> None:
    """RLIMIT_NPROC set edildiği ampirik doğrulanır (mock ile)."""
    calls: list[tuple[int, tuple[int, int]]] = []

    import types

    fake_resource = types.SimpleNamespace(
        RLIMIT_CPU=0,
        RLIMIT_AS=9,
        RLIMIT_NPROC=6,
        setrlimit=lambda which, lims: calls.append((which, lims)),
    )
    monkeypatch.setattr(actions_mod, "_resource", fake_resource)
    monkeypatch.delenv("ATLAS_SANDBOX_CPU_S", raising=False)
    monkeypatch.delenv("ATLAS_SANDBOX_MEM_MB", raising=False)
    monkeypatch.setenv("ATLAS_SANDBOX_MAX_PROC", "12")

    fn = _build_preexec_fn()
    assert fn is not None
    fn()  # child prosess içinde çağrılacak fonksiyon; test'te doğrudan.

    assert calls == [(6, (12, 12))]

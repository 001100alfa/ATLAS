"""SPEC 026.2 — Windows Job Objects testleri.

Windows-canlı: MEM limit ile bytearray patlaması gerçek subprocess ile
doğrulanır (`skipif non-Windows`). Non-Windows: dispatch no-op.
"""

from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

import pytest

from atlas_core.orchestrator.actions import (
    _apply_windows_job,
    _has_windows_sandbox_env,
    make_action,
)
from atlas_core.orchestrator.goals import Goal


def _goal_shell() -> Goal:
    return Goal(
        goal="win job sınır dene",
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


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_SANDBOX_MEM_MB", raising=False)
    monkeypatch.delenv("ATLAS_SANDBOX_MAX_PROC", raising=False)
    monkeypatch.delenv("ATLAS_SANDBOX_CPU_S", raising=False)


# ─────────────────────────────────────────────────────────────────────
# Non-Windows: dispatch no-op
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows guard")
def test_0262_non_windows_apply_donmes_false() -> None:
    """Non-Windows'ta _apply_windows_job her zaman False (dispatch no-op)."""
    assert _apply_windows_job(12345, 64, None) is False


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows guard")
def test_0262_non_windows_env_verili_yine_run_yolu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Non-Windows'ta env verilse de Job Objects yolu YOK — normal subprocess."""
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "64")
    action = make_action(_goal_shell(), tmp_path)
    obs, _ = action("shell:echo ok")
    assert "exit=0" in obs
    assert "ok" in obs


# ─────────────────────────────────────────────────────────────────────
# Env detection ortak
# ─────────────────────────────────────────────────────────────────────


def test_0262_env_yok_false(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _has_windows_sandbox_env() is False


def test_0262_mem_verili_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "64")
    assert _has_windows_sandbox_env() is True


def test_0262_max_proc_verili_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_MAX_PROC", "3")
    assert _has_windows_sandbox_env() is True


def test_0262_ikisi_de_verili_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "64")
    monkeypatch.setenv("ATLAS_SANDBOX_MAX_PROC", "3")
    assert _has_windows_sandbox_env() is True


# ─────────────────────────────────────────────────────────────────────
# Windows: bit-uyumlu (env yok)
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
def test_0262_windows_env_yok_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Env yok → mevcut subprocess.run yolu (bit-uyumlu 026/026.1)."""
    action = make_action(_goal_shell(), tmp_path)
    obs, _ = action("shell:cmd /c echo bit-uyumlu")
    assert "exit=0" in obs
    assert "bit-uyumlu" in obs


# ─────────────────────────────────────────────────────────────────────
# Windows canlı — MEM limit
# ─────────────────────────────────────────────────────────────────────


def _py_cmd() -> str:
    """PATH-tabanlı python komutu (mutlak yol shlex POSIX split'i bozar)."""
    for name in ("python", "python3", "py"):
        if shutil.which(name):
            return name
    pytest.skip("python PATH'te bulunamadı")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only canlı test")
def test_0262_windows_mem_limit_patlar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MEM_MB=64 iken 500 MB bytearray → subprocess ölür (exit != 0)."""
    py = _py_cmd()
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "64")
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "10.0")
    action = make_action(_goal_shell(), tmp_path)
    t0 = time.monotonic()
    obs, _ = action(
        f"shell:{py} -c \"x = bytearray(500 * 1024 * 1024); print(len(x))\""
    )
    elapsed = time.monotonic() - t0
    assert "exit=" in obs, obs
    exit_str = obs.split("exit=")[1].split()[0]
    exit_code = int(exit_str)
    assert exit_code != 0, f"MEM limit çalışmadı, exit={exit_code}, obs={obs}"
    # Timeout'a değil, memory limit'e takıldı
    assert elapsed < 8, f"limit çok yavaş: {elapsed:.1f}s"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only canlı test")
def test_0262_windows_mem_limit_altinda_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MEM_MB=256 + küçük alloc → başarılı (kısıt altında)."""
    py = _py_cmd()
    monkeypatch.setenv("ATLAS_SANDBOX_MEM_MB", "256")
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "10.0")
    action = make_action(_goal_shell(), tmp_path)
    obs, _ = action(f"shell:{py} -c \"print(sum(range(100)))\"")
    assert "exit=0" in obs, obs
    assert "4950" in obs


# ─────────────────────────────────────────────────────────────────────
# _apply_windows_job — env yok / non-Windows early-out
# ─────────────────────────────────────────────────────────────────────


def test_0262_apply_env_ikisi_de_none_false() -> None:
    """mem_mb=None VE max_proc=None → hemen False (syscall YOK)."""
    assert _apply_windows_job(1, None, None) is False


# ─────────────────────────────────────────────────────────────────────
# Windows: _apply_windows_job invalid pid → fail-safe uyarı
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
def test_0262_windows_invalid_pid_uyari(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Var olmayan pid (0xFFFFFFFF) → OpenProcess başarısız → uyarı + False."""
    ok = _apply_windows_job(0xFFFFFFFE, 64, None)
    assert ok is False
    err = capsys.readouterr().err
    assert "026.2" in err
    assert "başarısız" in err
    assert "WinError" in err


# ═════════════════════════════════════════════════════════════════════
# SPEC 026.3 — Windows CPU quota (JOB_OBJECT_LIMIT_PROCESS_TIME)
# ═════════════════════════════════════════════════════════════════════


def test_0263_env_cpu_s_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """`CPU_S` verilirse `_has_windows_sandbox_env` True döner (026.3)."""
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "3")
    assert _has_windows_sandbox_env() is True


def test_0263_apply_erken_cikis_uc_none() -> None:
    """`mem_mb=None VE max_proc=None VE cpu_s=None` → hemen False."""
    assert _apply_windows_job(1, None, None, None) is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only canlı test")
def test_0263_windows_cpu_quota_kesir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`CPU_S=1` iken sonsuz döngü CPU quota'da ölür (3.5 sn'den kısa)."""
    py = _py_cmd()
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "1")
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "8.0")  # timeout > cpu_s
    action = make_action(_goal_shell(), tmp_path)
    t0 = time.monotonic()
    obs, _ = action(f"shell:{py} -c \"while True: pass\"")
    elapsed = time.monotonic() - t0
    assert "exit=" in obs, obs
    exit_str = obs.split("exit=")[1].split()[0]
    exit_code = int(exit_str)
    assert exit_code != 0, f"CPU quota calışmadı, exit={exit_code}"
    # 3.5 sn'den kısa: CPU quota kesti, timeout değil
    assert elapsed < 3.5, f"CPU quota çok yavaş: {elapsed:.1f}s"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
def test_0263_windows_cpu_s_altinda_kucuk_i_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`CPU_S=5` + hafif iş → başarı (kısıt altında)."""
    py = _py_cmd()
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "5")
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "10.0")
    action = make_action(_goal_shell(), tmp_path)
    obs, _ = action(f"shell:{py} -c \"print(1+1)\"")
    assert "exit=0" in obs, obs
    assert "2" in obs


@pytest.mark.skipif(sys.platform == "win32", reason="Non-Windows")
def test_0263_non_windows_cpu_s_verili_run_yolu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Non-Windows: CPU_S verilirse Unix 026.1 RLIMIT_CPU yolu; Job Objects YOK."""
    monkeypatch.setenv("ATLAS_SANDBOX_CPU_S", "1")
    action = make_action(_goal_shell(), tmp_path)
    obs, _ = action("shell:echo unix-yol")
    assert "exit=0" in obs
    assert "unix-yol" in obs

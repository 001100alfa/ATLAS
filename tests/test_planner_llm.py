"""SPEC 003 — LLM (claude subprocess) planner testleri.

Subprocess'e gerçek erişim YOK: `subprocess.run` monkeypatch edilir.
Fabrika-zamanı hataları (bin yok) `_resolve_claude_bin` seviyesinde,
çağrı-zamanı hataları (timeout, exit!=0, boş) `_call_claude` içinde.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from atlas_core.orchestrator import planner as planner_mod
from atlas_core.orchestrator.goals import Goal
from atlas_core.orchestrator.planner import LLMPlannerError, make_planner


def _goal_llm() -> Goal:
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


class _FakeProc:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _prep_bin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Sahte bir 'claude' dosyası; ATLAS_LLM_CLAUDE_BIN olarak set edilir."""
    fake = tmp_path / "fake-claude.cmd"
    fake.write_text("@echo off\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_LLM", "claude")
    monkeypatch.setenv("ATLAS_LLM_CLAUDE_BIN", str(fake))
    return fake


# ---------- AC2: fabrika (bin bulunur) ----------

def test_fabrika_bin_env_ile_bulunur(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    plan = make_planner(_goal_llm())
    assert callable(plan)


def test_fabrika_bin_shutil_which_ile_bulunur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("ATLAS_LLM_CLAUDE_BIN", raising=False)
    monkeypatch.setenv("ATLAS_LLM", "claude")
    fake = tmp_path / "claude-in-path"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setattr(planner_mod.shutil, "which", lambda _name: str(fake))
    plan = make_planner(_goal_llm())
    assert callable(plan)


# ---------- AC3: bin yok = fabrika anında ----------

def test_bin_yok_fabrika_hata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_LLM_CLAUDE_BIN", raising=False)
    monkeypatch.setenv("ATLAS_LLM", "claude")
    monkeypatch.setattr(planner_mod.shutil, "which", lambda _name: None)
    with pytest.raises(LLMPlannerError, match="claude bulunamadı"):
        make_planner(_goal_llm())


def test_bin_env_yanlis_yol(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_LLM", "claude")
    monkeypatch.setenv("ATLAS_LLM_CLAUDE_BIN", str(tmp_path / "yok.cmd"))
    with pytest.raises(LLMPlannerError, match="dosya değil"):
        make_planner(_goal_llm())


# ---------- AC4: happy call ----------

def test_call_happy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        return _FakeProc(stdout="write:out.txt:1\n", returncode=0)

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    assert plan("goal", []) == "write:out.txt:1"


# ---------- AC5: timeout ----------

def test_call_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM_TIMEOUT", "3")

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        raise subprocess.TimeoutExpired(cmd="claude", timeout=3)

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match="timeout: 3s"):
        plan("goal", [])
    # kalıcı bozulma yok — ikinci çağrı da aynı hatayı verir
    with pytest.raises(LLMPlannerError, match="timeout"):
        plan("goal", [])


# ---------- AC6: non-zero exit ----------

def test_call_non_zero_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        return _FakeProc(stdout="", stderr="model overload", returncode=1)

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"exit=1.*model overload"):
        plan("goal", [])


def test_call_non_zero_exit_bos_stderr(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        return _FakeProc(stdout="", stderr="", returncode=2)

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"exit=2.*stderr boş"):
        plan("goal", [])


# ---------- AC7: boş cevap ----------

def test_call_bos_cevap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        return _FakeProc(stdout="   \n\n  ", returncode=0)

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match="boş plan"):
        plan("goal", [])


# ---------- AC8: çok satırlı cevap → ilk satır ----------

def test_call_cok_satirli_ilk_satir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        return _FakeProc(
            stdout="write:out.txt:hedef\nİkinci satır — açıklama\nÜçüncü\n",
            returncode=0,
        )

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    assert plan("goal", []) == "write:out.txt:hedef"


# ---------- AC9: UTF-8 sağlamlığı ----------

def test_call_utf8_turkce_ve_emoji(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        return _FakeProc(stdout="write:çıktı.txt:merhaba 🚀\n", returncode=0)

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    assert plan("goal", []) == "write:çıktı.txt:merhaba 🚀"


# ---------- AC11: bilinmeyen backend ----------

def test_backend_bilinmiyor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM", "gemini")
    with pytest.raises(NotImplementedError, match="gemini"):
        make_planner(_goal_llm())


# ---------- Prompt biçimi & OSError ----------

def test_prompt_history_gozlemleri_alir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    seen: dict[str, str] = {}

    def fake_run(*_args: Any, **kwargs: Any) -> _FakeProc:
        seen["input"] = kwargs.get("input", "")
        return _FakeProc(stdout="write:x.txt:1\n", returncode=0)

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    history = [
        (planner_mod.StepKind.PLAN, "write:x.txt:1"),
        (planner_mod.StepKind.OBSERVE, "wrote 1 byte"),
    ]
    plan("goal", history)
    assert "wrote 1 byte" in seen["input"]
    assert "write" in seen["input"]
    assert "dosya yaz" in seen["input"]


def test_call_oserror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_run(*_args: Any, **_kwargs: Any) -> _FakeProc:
        raise OSError("çalıştırılabilir değil")

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    plan = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match="başlatılamadı"):
        plan("goal", [])

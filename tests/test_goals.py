"""SPEC 002 §5 — Goal yükleyici testleri (Adım 3.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.orchestrator.goals import Goal, SpecError, load_goal

FIXTURES = Path(__file__).parent / "goals"


def test_hello_yaml_yuklenir() -> None:
    goal = load_goal(FIXTURES / "hello.yaml")
    assert isinstance(goal, Goal)
    assert goal.plan_kind == "static"
    assert goal.plan_steps == ("write:hello.txt:merhaba",)
    assert goal.action_allowlist == frozenset({"write"})
    assert goal.shell_allow_regex is None
    assert goal.judge_kind == "file_exists"
    assert goal.judge_arg == "hello.txt"
    assert goal.budget == 20.0
    assert goal.max_steps == 5
    # varsayılan cost tablosu korunur
    assert goal.costs == {"read": 1.0, "write": 2.0, "shell": 5.0}


def test_denied_shell_shell_regex_derlenir() -> None:
    goal = load_goal(FIXTURES / "denied_shell.yaml")
    assert goal.shell_allow_regex is not None
    assert goal.shell_allow_regex.fullmatch("echo merhaba")
    assert not goal.shell_allow_regex.fullmatch("rm -rf .")


def test_llm_stub_plan_steps_bos_olabilir() -> None:
    goal = load_goal(FIXTURES / "llm_stub.yaml")
    assert goal.plan_kind == "llm"
    assert goal.plan_steps == ()


def test_budget_costs_ozel_deger() -> None:
    goal = load_goal(FIXTURES / "budget.yaml")
    assert goal.budget == 3.0
    assert goal.costs["write"] == 2.0
    # dokunulmamış fiillerde varsayılan
    assert goal.costs["read"] == 1.0


def test_dosya_yoksa_spec_error() -> None:
    with pytest.raises(SpecError, match="bulunamadı"):
        load_goal(FIXTURES / "yok.yaml")


def test_eksik_alan_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "eksik.yaml"
    p.write_text("plan_kind: static\n", encoding="utf-8")
    with pytest.raises(SpecError, match="eksik alan.*goal"):
        load_goal(p)


def test_static_plan_steps_bos_olamaz(tmp_path: Path) -> None:
    p = tmp_path / "bos.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: []\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="static.*plan_steps"):
        load_goal(p)


def test_shell_allowlist_regex_zorunlu(tmp_path: Path) -> None:
    p = tmp_path / "shell_regex_yok.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"shell:echo x\"]\n"
        "action_allowlist: [shell]\njudge_kind: exit_zero\njudge_arg: \"\"\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="shell_allow_regex zorunlu"):
        load_goal(p)


def test_gecersiz_regex_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "kotu_regex.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"shell:echo x\"]\n"
        "action_allowlist: [shell]\nshell_allow_regex: \"[unclosed\"\n"
        "judge_kind: exit_zero\njudge_arg: \"\"\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="derlenemedi"):
        load_goal(p)


def test_bilinmeyen_fiil_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "kotu_fiil.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:x\"]\n"
        "action_allowlist: [read, exec]\n"
        "judge_kind: file_exists\njudge_arg: y\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="bilinmeyen fiil"):
        load_goal(p)


def test_bilinmeyen_plan_kind_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "kotu_plan.yaml"
    p.write_text(
        "goal: x\nplan_kind: telepathy\nplan_steps: []\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="plan_kind bilinmiyor"):
        load_goal(p)


def test_negatif_butce_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "kotu_butce.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "budget: -1\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="budget"):
        load_goal(p)


# ---------- SPEC 006: opsiyonel context alanları ----------


def test_006_default_inject_context_ve_limit() -> None:
    goal = load_goal(FIXTURES / "hello.yaml")
    # YAML'da yok — default kullanılır
    assert goal.inject_context is True
    assert goal.context_limit == 5


def test_006_inject_context_bool_degilse_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "inject_context: kırık\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="inject_context bool"):
        load_goal(p)


def test_006_context_limit_negatif_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "context_limit: -1\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="context_limit"):
        load_goal(p)


def test_006_context_limit_ust_sinir_spec_error(tmp_path: Path) -> None:
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "context_limit: 51\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="context_limit"):
        load_goal(p)


def test_006_context_limit_bool_reddedilir(tmp_path: Path) -> None:
    # bool int'in alt sınıfı — özel kontrol testi
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "context_limit: true\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="context_limit"):
        load_goal(p)


# ---------- SPEC 003.2: opsiyonel llm_prompt ----------


def test_003_2_llm_prompt_alan_yok_none(tmp_path: Path) -> None:
    """AC1: llm_prompt anahtarı yok → goal.llm_prompt is None."""
    goal = load_goal(FIXTURES / "hello.yaml")
    assert goal.llm_prompt is None


def test_003_2_llm_prompt_null_none(tmp_path: Path) -> None:
    """AC2: llm_prompt: null → None."""
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "llm_prompt: null\n",
        encoding="utf-8",
    )
    assert load_goal(p).llm_prompt is None


def test_003_2_llm_prompt_bos_string_none(tmp_path: Path) -> None:
    """AC3: llm_prompt: "" → None (sessiz fallback)."""
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        'llm_prompt: ""\n',
        encoding="utf-8",
    )
    assert load_goal(p).llm_prompt is None


def test_003_2_llm_prompt_gecerli_string() -> None:
    """AC4: llm_prompt: "Sen ATLAS'ın..." → aynen string."""
    goal = load_goal(FIXTURES / "llm_custom_prompt.yaml")
    assert isinstance(goal.llm_prompt, str)
    assert "kıdemli mühendis planlayıcısısın" in goal.llm_prompt
    assert "EN 1993" in goal.llm_prompt


def test_003_2_llm_prompt_tip_hatasi_int(tmp_path: Path) -> None:
    """AC5: llm_prompt: 42 → SpecError."""
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "llm_prompt: 42\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="llm_prompt string olmalı"):
        load_goal(p)


def test_003_2_llm_prompt_tip_hatasi_liste(tmp_path: Path) -> None:
    p = tmp_path / "b.yaml"
    p.write_text(
        "goal: x\nplan_kind: static\nplan_steps: [\"read:y\"]\n"
        "action_allowlist: [read]\njudge_kind: file_exists\njudge_arg: y\n"
        "llm_prompt: [a, b]\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecError, match="llm_prompt string olmalı"):
        load_goal(p)

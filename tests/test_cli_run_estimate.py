"""SPEC 069 — atlas run --estimate LLM'siz cost tahmini testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import _estimate_run_cost, main


def _make_goal_yaml(tmp_path: Path, name: str, budget: float = 50.0,
                    max_steps: int = 8) -> Path:
    p = tmp_path / f"{name}.yaml"
    p.write_text(
        f"goal: test hedef {name}\n"
        f"plan_kind: static\n"
        f"plan_steps:\n"
        f'  - "write:x.txt:hello"\n'
        f"action_allowlist: [write]\n"
        f"judge_kind: file_exists\n"
        f'judge_arg: "x.txt"\n'
        f"budget: {budget}\n"
        f"max_steps: {max_steps}\n",
        encoding="utf-8",
    )
    return p


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.delenv("ATLAS_ESTIMATE_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("ATLAS_LLM_PRICE_IN_PER_1M", raising=False)
    monkeypatch.delenv("ATLAS_LLM_PRICE_OUT_PER_1M", raising=False)


# ═════════════════════════════════════════════════════════════════════
# _estimate_run_cost (birim)
# ═════════════════════════════════════════════════════════════════════


class _FakeGoal:
    """Basit goal stub — sadece attribute'lar."""
    def __init__(self, goal: str, max_steps: int, budget: float):
        self.goal = goal
        self.max_steps = max_steps
        self.budget = budget


def test_069_estimate_stub_backend_cost_sifir() -> None:
    """Stub backend → LLM yok → cost 0."""
    g = _FakeGoal("test", max_steps=10, budget=50.0)
    result = _estimate_run_cost(g, "stub", 500, 3.0, 15.0)
    assert result["backend"] == "stub"
    assert result["estimated_cost_usd"] == 0.0
    assert result["estimated_total_tokens"] == 5000  # 10 * 500


def test_069_estimate_fiyat_yok_cost_sifir() -> None:
    """Anthropic ama fiyat env yok → cost 0."""
    g = _FakeGoal("test", max_steps=5, budget=50.0)
    result = _estimate_run_cost(g, "anthropic", 500, 0.0, 0.0)
    assert result["estimated_cost_usd"] == 0.0


def test_069_estimate_anthropic_fiyat_hesaplanir() -> None:
    """Anthropic + fiyat env → cost hesaplanır."""
    g = _FakeGoal("test", max_steps=8, budget=50.0)
    result = _estimate_run_cost(g, "anthropic", 1000, 3.0, 15.0)
    # 8 * 1000 = 8000 tokens; yarı input yarı output
    # cost = (4000 * 3 + 4000 * 15) / 1_000_000 = 0.072
    assert result["estimated_total_tokens"] == 8000
    assert result["estimated_cost_usd"] == 0.072


def test_069_estimate_max_steps_uygulanir() -> None:
    """max_steps değişince total_tokens ve cost değişir."""
    g5 = _FakeGoal("t", max_steps=5, budget=50.0)
    g20 = _FakeGoal("t", max_steps=20, budget=50.0)
    r5 = _estimate_run_cost(g5, "anthropic", 100, 1.0, 1.0)
    r20 = _estimate_run_cost(g20, "anthropic", 100, 1.0, 1.0)
    assert r20["estimated_total_tokens"] == 4 * r5["estimated_total_tokens"]


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas run --estimate
# ═════════════════════════════════════════════════════════════════════


def test_069_cli_estimate_insan_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    goal = _make_goal_yaml(tmp_path, "g1")
    rc = main([
        "run", "--goal-file", str(goal), "--estimate",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS run --estimate" in out
    assert "backend:" in out
    assert "max_steps:" in out
    assert "tahmini token:" in out
    assert "tahmini cost:" in out


def test_069_cli_estimate_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    goal = _make_goal_yaml(tmp_path, "g1", max_steps=5)
    rc = main([
        "run", "--goal-file", str(goal), "--estimate", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["max_steps"] == 5
    assert "estimated_cost_usd" in data
    assert "estimated_total_tokens" in data


def test_069_cli_estimate_llm_cagrilmaz_audit_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--estimate → audit dosyasına 'atlas-run' kaydı DÜŞMEZ (LLM yok)."""
    _env(monkeypatch, tmp_path)
    goal = _make_goal_yaml(tmp_path, "g1")
    rc = main([
        "run", "--goal-file", str(goal), "--estimate",
    ])
    assert rc == 0
    audit_path = tmp_path / "audit.jsonl"
    # audit.jsonl ya hiç oluşmadı ya boş
    if audit_path.exists():
        content = audit_path.read_text(encoding="utf-8")
        assert "atlas-run" not in content


def test_069_cli_estimate_env_tokens_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_ESTIMATE_TOKENS_PER_CALL", "2000")
    goal = _make_goal_yaml(tmp_path, "g1", max_steps=3)
    rc = main([
        "run", "--goal-file", str(goal), "--estimate", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tokens_per_call"] == 2000
    assert data["estimated_total_tokens"] == 6000  # 3 * 2000


def test_069_cli_estimate_gecersiz_env_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_ESTIMATE_TOKENS_PER_CALL", "not-int")
    goal = _make_goal_yaml(tmp_path, "g1", max_steps=3)
    rc = main([
        "run", "--goal-file", str(goal), "--estimate", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tokens_per_call"] == 500  # fallback default


def test_069_cli_run_default_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--estimate yoksa mevcut atlas run <goal> echo demo bit-uyumlu."""
    _env(monkeypatch, tmp_path)
    rc = main(["run", "test hedef", "--steps", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "done=True" in out
    assert "--estimate" not in out


def test_069_cli_estimate_bozuk_goal_yaml_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--estimate + bozuk YAML → SPEC HATASI exit 2 (LLM'ye ulaşmaz)."""
    _env(monkeypatch, tmp_path)
    bad = tmp_path / "bad.yaml"
    bad.write_text("this: is: not: valid", encoding="utf-8")
    rc = main([
        "run", "--goal-file", str(bad), "--estimate",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err

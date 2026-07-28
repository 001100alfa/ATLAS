"""In-process CLI çağrıları — subprocess coverage boşluğunu kapatır."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    os.makedirs(tmp_path / "v", exist_ok=True)


def test_workflow_run_happy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    y = tmp_path / "w.yaml"
    y.write_text(
        "name: t\nsteps:\n"
        "  - uses: pipeline.gate\n    with: {file: pyproject.toml}\n",
        encoding="utf-8",
    )
    assert main(["workflow", "run", str(y)]) == 0


def test_workflow_run_handler_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    y = tmp_path / "w.yaml"
    y.write_text(
        "name: t\nsteps:\n  - uses: pipeline.gate\n    with: {file: yok.md}\n",
        encoding="utf-8",
    )
    assert main(["workflow", "run", str(y)]) == 6


def test_workflow_run_workflow_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    y = tmp_path / "w.yaml"
    y.write_text("name: t\nsteps:\n  - uses: bogus.step\n", encoding="utf-8")
    assert main(["workflow", "run", str(y)]) == 6


def test_workflow_yaml_yok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["workflow", "run", str(tmp_path / "yok.yaml")]) == 2


def test_workflow_dry_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    y = tmp_path / "w.yaml"
    y.write_text(
        "name: t\nsteps:\n  - uses: pipeline.test\n    with: {paths: [tests/test_goals.py]}\n",
        encoding="utf-8",
    )
    assert main(["workflow", "run", str(y), "--dry-run"]) == 0


def test_run_goal_file_hello(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["run", "--goal-file", "tests/goals/hello.yaml", "--run-id", "d"]) == 0


def test_run_goal_denied(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["run", "--goal-file", "tests/goals/denied_verb.yaml", "--run-id", "d"]) == 5


def test_run_goal_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["run", "--goal-file", "tests/goals/budget.yaml", "--run-id", "d"]) == 3


def test_run_goal_spec_hatasi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    bad = tmp_path / "b.yaml"
    bad.write_text("plan_kind: static\n", encoding="utf-8")
    assert main(["run", "--goal-file", str(bad)]) == 2


def test_run_llm_stub_denied(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    assert main(["run", "--goal-file", "tests/goals/llm_stub.yaml", "--run-id", "d"]) == 5


def test_run_echo_demo_regresyon(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["run", "eski hedef", "--steps", "1", "--budget", "50", "--step-cost", "5"]) == 0


def test_run_ne_goal_ne_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["run"]) == 2


def test_scan_temiz(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    (tmp_path / "clean.py").write_text("x = 1\n")
    assert main(["scan", str(tmp_path)]) == 0


def test_scan_sir_bulur(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    (tmp_path / "leak.py").write_text('api_key = "supersecret123456"\n')
    assert main(["scan", str(tmp_path)]) == 1


def test_scan_tek_dosya(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    assert main(["scan", str(f)]) == 0


def test_audit_verify_bos(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["audit-verify"]) == 0


def test_reindex_partial(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    (tmp_path / "v" / "entities").mkdir(parents=True, exist_ok=True)
    (tmp_path / "v" / "entities" / "a.md").write_text("içerik burada", encoding="utf-8")
    assert main(["reindex"]) == 0


def test_reindex_full(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["reindex", "--full"]) == 0


def test_recall_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    main(["remember", "kesit", "I-kesit formülleri"])
    assert main(["recall", "kesit"]) == 0


def test_recall_cli_bos(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    assert main(["recall", "hicyokk"]) == 0


def test_context_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _env(monkeypatch, tmp_path)
    main(["remember", "kesit", "I-kesit formülleri"])
    assert main(["context", "kesit"]) == 0


def test_audit_verify_bozuk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    audit = tmp_path / "a.jsonl"
    audit.write_text('{"ts":"x","actor":"a","action":"b","detail":"c","prev":"WRONG","hash":"deadbeef"}\n')
    monkeypatch.setenv("ATLAS_AUDIT", str(audit))
    assert main(["audit-verify"]) == 1

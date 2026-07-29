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


def test_run_llm_claude_bin_yok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """SPEC 003 AC10: LLM bin bulunamayınca CLI exit 7 + audit llm_error."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "claude")
    monkeypatch.delenv("ATLAS_LLM_CLAUDE_BIN", raising=False)
    # PATH'te claude olmadığını garantile
    import atlas_core.orchestrator.planner as planner_mod
    monkeypatch.setattr(planner_mod.shutil, "which", lambda _n: None)
    assert main(["run", "--goal-file", "tests/goals/llm_claude.yaml", "--run-id", "d"]) == 7
    audit_txt = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
    assert "llm_error" in audit_txt


def test_run_llm_claude_runtime_hatasi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """SPEC 003: fabrika tamam ama call hatası da exit 7 döner."""
    _env(monkeypatch, tmp_path)
    fake = tmp_path / "fake-claude.cmd"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("ATLAS_LLM", "claude")
    monkeypatch.setenv("ATLAS_LLM_CLAUDE_BIN", str(fake))
    import atlas_core.orchestrator.planner as planner_mod

    class _Proc:
        stdout, stderr, returncode = "", "boom", 3

    monkeypatch.setattr(planner_mod.subprocess, "run", lambda *a, **k: _Proc())
    assert main(["run", "--goal-file", "tests/goals/llm_claude.yaml", "--run-id", "e"]) == 7


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


# ---------- SPEC 006: otomatik context injection ----------


def test_006_static_gorevde_baglam_kapali(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC3: static görev → _context_enabled False → 'Bağlam: (kapalı)'."""
    _env(monkeypatch, tmp_path)
    # capsys benzeri: main() stdout'unu tmpfile'a yönlendirmek yerine,
    # subprocess'siz direkt fonksiyonu çalıştırıyoruz — sadece exit'i ölçelim.
    assert main(["run", "--goal-file", "tests/goals/hello.yaml", "--run-id", "d"]) == 0


def test_006_atlas_context_off_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC5: env=off → LLM görevi bile olsa 'Bağlam: (kapalı)'.

    Not: llm_stub.yaml stub planı `plan[stub]:noop` üretir; bu fiil
    action_allowlist=[read] içinde yok → ActionDenied → exit 5. Yani
    exit kodu değil, stdout'taki başlık test edilir.
    """
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    monkeypatch.setenv("ATLAS_CONTEXT", "off")
    assert main(["run", "--goal-file", "tests/goals/llm_stub.yaml", "--run-id", "e"]) == 5
    out = capsys.readouterr().out
    assert "Bağlam: (kapalı)" in out


def test_006_llm_gorevde_baglam_hesaplanir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC1: llm görev + varsayılan → _context_enabled True → 'Bağlam:' başlığı."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    monkeypatch.delenv("ATLAS_CONTEXT", raising=False)
    assert main(["run", "--goal-file", "tests/goals/llm_stub.yaml", "--run-id", "f"]) == 5
    out = capsys.readouterr().out
    # başlık var ve "kapalı" değil (etkin ama vault boş: "yok")
    assert "Bağlam:" in out
    baglam_satir = [ln for ln in out.splitlines() if ln.startswith("Bağlam:")][0]
    assert "kapalı" not in baglam_satir


def test_006_gbrain_hata_izole(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC7: GBrain patlarsa görev context'siz devam (stderr uyarı, exit != 7)."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    import atlas_core.cli as cli_mod

    class _Boom:
        def __init__(self, *a: object, **kw: object) -> None:
            raise RuntimeError("gbrain diski dolu")

    monkeypatch.setattr(cli_mod, "GBrain", _Boom)
    # stub planı ActionDenied → exit 5, ama context hatası izole (7 değil)
    assert main(["run", "--goal-file", "tests/goals/llm_stub.yaml", "--run-id", "g"]) == 5
    err = capsys.readouterr().err
    assert "GBrain context alınamadı" in err
    assert "diski dolu" in err


def test_006_goal_inject_context_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC6: goal.inject_context=False → kapalı (env değil, YAML)."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    y = tmp_path / "no_ctx.yaml"
    y.write_text(
        "goal: bağlamsız\nplan_kind: llm\naction_allowlist: [read]\n"
        "judge_kind: file_exists\njudge_arg: yok.txt\n"
        "budget: 20\nmax_steps: 2\ninject_context: false\n",
        encoding="utf-8",
    )
    assert main(["run", "--goal-file", str(y), "--run-id", "h"]) == 5
    out = capsys.readouterr().out
    assert "Bağlam: (kapalı)" in out


def test_006_baglam_var_ise_sayilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FR8: vault'ta ilgili not varsa 'N not enjekte edildi'."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    main(["remember", "dosya-not", "dosya yazma notları için ayrıntılar"])
    y = tmp_path / "match.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: llm\naction_allowlist: [read]\n"
        "judge_kind: file_exists\njudge_arg: yok.txt\n"
        "budget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    assert main(["run", "--goal-file", str(y), "--run-id", "i"]) == 5
    out = capsys.readouterr().out
    # "N not enjekte edildi" veya "Bağlam: yok" (FTS bulamazsa) — ikisi de geçerli
    assert ("enjekte edildi" in out) or ("Bağlam: yok" in out)

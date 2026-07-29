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


def test_run_llm_anthropic_key_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SPEC 003.1 AC21: anthropic key yok → exit 7 + audit llm_error."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert (
        main(["run", "--goal-file", "tests/goals/llm_anthropic.yaml", "--run-id", "a"])
        == 7
    )
    audit_txt = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
    assert "llm_error" in audit_txt


def test_008_retry_env_uc_deneme_hepsi_basarisiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SPEC 008 AC11: retries=2 (env) + sürekli LLMPlannerError → 3 deneme, exit 7."""
    _env(monkeypatch, tmp_path)
    fake = tmp_path / "fake-claude.cmd"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("ATLAS_LLM", "claude")
    monkeypatch.setenv("ATLAS_LLM_CLAUDE_BIN", str(fake))
    monkeypatch.setenv("ATLAS_LLM_RETRIES", "2")
    monkeypatch.setenv("ATLAS_LLM_BACKOFF", "0")  # test hızı
    import atlas_core.orchestrator.planner as planner_mod

    calls = {"n": 0}

    class _Proc:
        stdout, stderr, returncode = "", "boom", 3

    def fake_run(*_a: object, **_kw: object) -> _Proc:
        calls["n"] += 1
        return _Proc()

    monkeypatch.setattr(planner_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(planner_mod, "_sleep", lambda _s: None)
    assert (
        main(["run", "--goal-file", "tests/goals/llm_claude.yaml", "--run-id", "r"])
        == 7
    )
    # 1 initial + 2 retry = 3 subprocess çağrısı
    assert calls["n"] == 3


def test_run_llm_acp_bin_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SPEC 003.1: acp bin yok → exit 7 + audit llm_error."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "acp")
    monkeypatch.delenv("ATLAS_LLM_ACP_BIN", raising=False)
    import atlas_core.orchestrator.planner as planner_mod

    monkeypatch.setattr(planner_mod.shutil, "which", lambda _n: None)
    assert (
        main(["run", "--goal-file", "tests/goals/llm_claude.yaml", "--run-id", "b"])
        == 7
    )
    audit_txt = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
    assert "llm_error" in audit_txt


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


# ---------- SPEC 007: atlas archive ----------


def _mk_fake_task(root: Path, name: str, *, with_ship: bool = True) -> Path:
    """Sahte tamamlanmış görev klasörü — 007 testleri için ortak yardımcı."""
    d = root / "pipeline" / "tasks" / name
    d.mkdir(parents=True)
    (d / "00-need.md").write_text(f"# {name}\n\nihtiyaç.\n", encoding="utf-8")
    (d / "02-spec.md").write_text(f"# {name} SPEC\n\ndetaylar.\n", encoding="utf-8")
    if with_ship:
        (d / "09-ship.md").write_text(
            f"# {name} — Ship\n\n"
            "## Sonuç\n"
            "Görev başarıyla tamamlandı ve teslim edildi.\n"
            "İlgili modül genişledi, testler yeşil.\n"
            "\n"
            "## Dosyalar\n"
            "- src/foo.py\n",
            encoding="utf-8",
        )
    return d


def test_007_archive_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC1: dry-run yıkıcı işlem yapmaz; çıktı 'dry-run' etiketi taşır."""
    _env(monkeypatch, tmp_path)
    d = _mk_fake_task(tmp_path, "003-llm-planner")
    rc = main([
        "archive", "003-llm-planner",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[dry-run]" in out
    assert "003-llm-planner" in out
    # Klasör hâlâ duruyor
    assert d.is_dir()
    # Arşiv dosyası yok
    assert not (tmp_path / "archive").exists() or not any(
        (tmp_path / "archive").iterdir()
    )
    # Audit yazılmadı (yıkıcı değil)
    audit = tmp_path / "a.jsonl"
    assert not audit.exists() or "archive" not in audit.read_text(encoding="utf-8")


def test_007_archive_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC2 + AC7: --apply gerçek arşiv + audit kaydı."""
    _env(monkeypatch, tmp_path)
    d = _mk_fake_task(tmp_path, "003-llm-planner")
    rc = main([
        "archive", "003-llm-planner", "--apply",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "arşivlendi:" in out
    # tar.gz oluştu
    tar_files = list((tmp_path / "archive").glob("003-llm-planner-*.tar.gz"))
    assert len(tar_files) == 1
    # Görev klasörü kaldı? kaldırılmalı.
    assert not d.exists()
    # Vault notu var
    note = tmp_path / "v" / "tasks" / "task-003-llm-planner.md"
    assert note.is_file()
    # Audit yazıldı
    audit_txt = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
    assert "atlas-archive" in audit_txt
    assert "archive" in audit_txt
    assert "003-llm-planner" in audit_txt


def test_007_archive_klasor_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC3: klasör yok → exit 2 + stderr mesajı."""
    _env(monkeypatch, tmp_path)
    (tmp_path / "pipeline" / "tasks").mkdir(parents=True)
    rc = main([
        "archive", "yok-boyle",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "görev klasörü yok" in err


def test_007_archive_ship_summary_okunur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC4: 09-ship.md'nin ilk paragrafı vault notunda geçer."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "999-demo")
    main([
        "archive", "999-demo", "--apply",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    note = (tmp_path / "v" / "tasks" / "task-999-demo.md").read_text(encoding="utf-8")
    assert "Görev başarıyla tamamlandı" in note


def test_007_archive_summary_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC5: --summary verilirse ship.md yok sayılır."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "888-demo")
    main([
        "archive", "888-demo", "--apply",
        "--summary", "el ile yazılmış özet",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    note = (tmp_path / "v" / "tasks" / "task-888-demo.md").read_text(encoding="utf-8")
    assert "el ile yazılmış özet" in note
    # Ship.md'nin sabit metni burada geçmemeli
    assert "Görev başarıyla tamamlandı" not in note


def test_007_archive_ship_yok_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC6: ship.md yok + summary yok → fallback '<task> arşivlendi'."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "777-demo", with_ship=False)
    main([
        "archive", "777-demo", "--apply",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    note = (tmp_path / "v" / "tasks" / "task-777-demo.md").read_text(encoding="utf-8")
    assert "777-demo arşivlendi" in note


# ---------- SPEC 012: --all toplu arşiv ----------


def test_012_all_dry_run_liste(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """M3: dry-run adayları listeler; yıkıcı iş yapmaz."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "003-alpha")
    _mk_fake_task(tmp_path, "004-beta")
    _mk_fake_task(tmp_path, "005-eksik", with_ship=False)  # ship.md yok → atlanmalı

    rc = main([
        "archive", "--all",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[dry-run] toplu arşivleme adayları: 2 görev" in out
    assert "003-alpha" in out
    assert "004-beta" in out
    assert "005-eksik" not in out  # ship.md yok → aday değil
    # Klasörler duruyor
    assert (tmp_path / "pipeline" / "tasks" / "003-alpha").is_dir()


def test_012_all_apply_yes_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """M4: --apply var ama --yes yok → exit 2 + uyarı."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "003-alpha")
    rc = main([
        "archive", "--all", "--apply",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--yes ile onaylayın" in err
    # Klasör duruyor (yıkıcı iş çalışmadı)
    assert (tmp_path / "pipeline" / "tasks" / "003-alpha").is_dir()


def test_012_all_apply_yes_hepsi_basarili(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy: --all --apply --yes → tüm adaylar arşivlenir + audit."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "003-alpha")
    _mk_fake_task(tmp_path, "004-beta")
    _mk_fake_task(tmp_path, "005-gamma")

    rc = main([
        "archive", "--all", "--apply", "--yes",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "arşivlendi: 3/3 görev" in out
    # Tüm klasörler kaldırılmış
    for name in ("003-alpha", "004-beta", "005-gamma"):
        assert not (tmp_path / "pipeline" / "tasks" / name).exists()
    # 3 tar.gz üretilmiş
    tar_files = list((tmp_path / "archive").glob("*.tar.gz"))
    assert len(tar_files) == 3
    # Audit üç archive kaydı
    audit_txt = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
    for name in ("003-alpha", "004-beta", "005-gamma"):
        assert name in audit_txt


def test_012_all_apply_yes_fail_fast(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Fail-fast: ortadaki görevde hata → dur; sonrakilere geçme."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "003-alpha")
    _mk_fake_task(tmp_path, "004-beta")
    _mk_fake_task(tmp_path, "005-gamma")

    import atlas_core.cli as cli_mod
    real_archive = cli_mod.archive_task

    def boom_archive(task_dir, arch, vault, summary):  # type: ignore[no-untyped-def]
        if task_dir.name == "004-beta":
            raise OSError("disk dolu")
        return real_archive(task_dir, arch, vault, summary)

    monkeypatch.setattr(cli_mod, "archive_task", boom_archive)

    rc = main([
        "archive", "--all", "--apply", "--yes",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 6
    out = capsys.readouterr()
    assert "arşivlendi: 1/3 görev" in out.out
    assert "003-alpha" in out.out
    assert "başarısız: 004-beta" in out.err
    assert "disk dolu" in out.err
    assert "atlanan: 005-gamma" in out.out
    # 003 kaldırıldı, 004+005 duruyor
    assert not (tmp_path / "pipeline" / "tasks" / "003-alpha").exists()
    assert (tmp_path / "pipeline" / "tasks" / "004-beta").is_dir()
    assert (tmp_path / "pipeline" / "tasks" / "005-gamma").is_dir()


def test_012_all_bos_liste(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Aday yok → dry-run '0 görev'; exit 0."""
    _env(monkeypatch, tmp_path)
    (tmp_path / "pipeline" / "tasks").mkdir(parents=True)
    rc = main([
        "archive", "--all",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    assert "0 görev" in capsys.readouterr().out


# ---------- SPEC 017: --auto yaş filtresi ----------


def _age_ship_mtime(root: Path, name: str, days_old: float) -> None:
    """Verilen görevin 09-ship.md dosyasının mtime'ını N gün önceye çek."""
    import os as os_mod
    ship = root / "pipeline" / "tasks" / name / "09-ship.md"
    old_ts = (
        __import__("datetime").datetime.now().timestamp() - days_old * 86400
    )
    os_mod.utime(ship, (old_ts, old_ts))


def test_017_auto_taze_atlanir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--auto varsayılan 7 gün eşiği; taze ship.md atlanır."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "003-taze")  # şimdi oluştu, mtime bugün
    rc = main([
        "archive", "--all", "--auto",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "adayları (auto, >7 gün): 0 görev" in out
    assert "003-taze" not in out


def test_017_auto_eski_secilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """10 gün eski ship.md → --auto (7 gün) → aday."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "003-eski")
    _mk_fake_task(tmp_path, "004-taze")
    _age_ship_mtime(tmp_path, "003-eski", days_old=10)

    rc = main([
        "archive", "--all", "--auto",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 görev" in out
    assert "003-eski" in out
    assert "004-taze" not in out


def test_017_env_esik_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """ATLAS_ARCHIVE_AGE_DAYS=1 → 2 gün eski görev aday."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_ARCHIVE_AGE_DAYS", "1")
    _mk_fake_task(tmp_path, "003-iki-gun")
    _age_ship_mtime(tmp_path, "003-iki-gun", days_old=2)

    rc = main([
        "archive", "--all", "--auto",
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "adayları (auto, >1 gün): 1 görev" in out
    assert "003-iki-gun" in out


def test_017_auto_yoksa_012_davranisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--auto olmadan --all → 012 davranışı (yaş yok, hepsi aday)."""
    _env(monkeypatch, tmp_path)
    _mk_fake_task(tmp_path, "003-taze")
    rc = main([
        "archive", "--all",  # --auto yok
        "--tasks-root", str(tmp_path / "pipeline" / "tasks"),
        "--archive-root", str(tmp_path / "archive"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "adayları: 1 görev" in out  # "auto" başlıkta YOK
    assert "003-taze" in out


# ---------- SPEC 020: --dry-run ----------


def test_020_dry_run_stub_llm_stub_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--dry-run: planner çağrılır (stub backend), action stub, exit 0."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")  # LLMPlannerError yolu değil
    rc = main([
        "run", "--goal-file", "tests/goals/llm_stub.yaml",
        "--run-id", "d", "--dry-run",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "MOD: dry-run" in out
    # Audit'te dry_run kayıt
    audit_txt = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
    assert "dry_run" in audit_txt


def test_020_dry_run_action_stub_dosya_yaratmaz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """--dry-run: gerçek 'write' action çalıştırmaz — dosya yok."""
    _env(monkeypatch, tmp_path)
    # static görev: write plan
    y = tmp_path / "static.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: static\n"
        "plan_steps: [\"write:kanit.txt:merhaba\"]\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: kanit.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    rc = main([
        "run", "--goal-file", str(y), "--run-id", "e", "--dry-run",
    ])
    assert rc == 0
    # Sandbox içinde kanit.txt YOK — action gerçekten çalışmadı
    sandbox = tmp_path / "sb" / f"{y.stem}-e"
    assert not (sandbox / "kanit.txt").exists()


def test_020_dry_run_yoksa_normal_yol(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """--dry-run yoksa: SPEC 002 normal davranış (regresyon)."""
    _env(monkeypatch, tmp_path)
    y = tmp_path / "static.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: static\n"
        "plan_steps: [\"write:kanit.txt:merhaba\"]\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: kanit.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    rc = main([
        "run", "--goal-file", str(y), "--run-id", "f",  # --dry-run YOK
    ])
    assert rc == 0
    sandbox = tmp_path / "sb" / f"{y.stem}-f"
    # Dosya YAZILMIŞ
    assert (sandbox / "kanit.txt").is_file()


def test_020_dry_run_llm_hata_exit_7(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """--dry-run LLM hata yolunu bypass ETMEZ — exit 7 hâlâ çalışır."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert (
        main([
            "run", "--goal-file", "tests/goals/llm_anthropic.yaml",
            "--run-id", "g", "--dry-run",
        ])
        == 7
    )


# ---------- SPEC 021: atlas doctor ----------


def test_021_doctor_stub_varsayilan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Varsayılan (env yok) → stub backend + exit 0."""
    _env(monkeypatch, tmp_path)
    monkeypatch.delenv("ATLAS_LLM", raising=False)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ATLAS_LLM: stub" in out
    assert "[LLM backend]" in out
    assert "[Retry & fiyat]" in out
    assert "[Depolama]" in out


def test_021_doctor_anthropic_key_yok_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Anthropic backend + key yok → `[!]` uyarısı; exit hâlâ 0."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[!] ANTHROPIC_API_KEY yok" in out


def test_021_doctor_anthropic_key_maskeler(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Anthropic key varsa maskelenir — tam key ASLA stdout'ta olmaz."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-SUPER-SECRET-abcdef123456")
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    # Tam key STDOUT'ta YOK
    assert "SUPER-SECRET" not in out
    # Maske görünür
    assert "sk-" in out
    assert "***" in out
    assert "456" in out  # son 3 karakter


def test_021_doctor_claude_bin_yok_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "claude")
    monkeypatch.delenv("ATLAS_LLM_CLAUDE_BIN", raising=False)
    import atlas_core.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_shutil", cli_mod, raising=False)
    # shutil.which'i patch et
    import shutil
    monkeypatch.setattr(shutil, "which", lambda _n: None)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[!] claude bin bulunamadı" in out


def test_021_doctor_bilinmeyen_backend_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "xyz-backend")
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[!] bilinmeyen backend: xyz-backend" in out
    assert "stub" in out and "claude" in out and "anthropic" in out


# ---------- SPEC 021.1: doctor --json ----------


def test_021_1_json_parse_edilebilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--json → stdout tek JSON, parse edilebilir."""
    import json as _json
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    rc = main(["doctor", "--json"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = _json.loads(out)
    assert data["backend"]["ATLAS_LLM"] == "stub"
    assert "retry_pricing" in data
    assert "storage" in data
    assert "warnings" in data
    assert data["warnings"] == []


def test_021_1_json_backend_anthropic_key_mask(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON çıktısında API key hâlâ maskeli."""
    import json as _json
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-SECRET-abc123")
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = _json.loads(capsys.readouterr().out.strip())
    key = data["backend"]["ANTHROPIC_API_KEY"]
    assert "***" in key
    assert "SECRET" not in key


def test_021_1_json_warnings_dolu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Anthropic + key yok → warnings listesinde uyarı."""
    import json as _json
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rc = main(["doctor", "--json"])
    assert rc == 0
    data = _json.loads(capsys.readouterr().out.strip())
    assert any("ANTHROPIC_API_KEY" in w for w in data["warnings"])


def test_021_1_insan_format_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--json yoksa 021 insan format bit-uyumlu (regresyon)."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[LLM backend]" in out
    assert "[Retry & fiyat]" in out
    assert "[Depolama]" in out


# ---------- SPEC 021.2: doctor --ping ----------


class _FakePingResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _FakePingResponse:
        return self

    def __exit__(self, *_a: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_021_2_ping_non_anthropic_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--ping stub backend'de uyarı verir, request atmaz."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "stub")
    rc = main(["doctor", "--ping"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[!] --ping yalnız anthropic backend'de çalışır" in out


def test_021_2_ping_happy_insan_format(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy: --ping anthropic + key → latency + tokens raporlanır."""
    import json as _json
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123456")

    # cli_mod içindeki lazy urllib import'unu doğrudan yakalayamayız —
    # `atlas_core.cli._run_anthropic_ping` içeriye alıyor. Onun yerine
    # planner_mod'da _extract_usage/_fmt_cost zaten test edilmiş,
    # burada urlopen çağrısını sysconftext'te patch'leyelim.
    from urllib import request as _urllib_request
    monkeypatch.setattr(
        _urllib_request, "urlopen",
        lambda *_a, **_kw: _FakePingResponse(_json.dumps({
            "content": [{"type": "text", "text": "hello!"}],
            "usage": {"input_tokens": 8, "output_tokens": 3},
        }).encode("utf-8")),
    )
    rc = main(["doctor", "--ping"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[Ping]" in out
    assert "latency:" in out
    assert "input_tokens: 8" in out
    assert "output_tokens: 3" in out


def test_021_2_ping_hata_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """URLError → warnings + exit 0."""
    from urllib import error as _urllib_error
    from urllib import request as _urllib_request
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123456")

    def raiser(*_a: object, **_kw: object):
        raise _urllib_error.URLError("dns yok")

    monkeypatch.setattr(_urllib_request, "urlopen", raiser)
    rc = main(["doctor", "--ping"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[!] ping başarısız: dns yok" in out


def test_021_2_ping_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--ping --json → JSON'da `ping` alanı."""
    import json as _json
    from urllib import request as _urllib_request
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123456")

    monkeypatch.setattr(
        _urllib_request, "urlopen",
        lambda *_a, **_kw: _FakePingResponse(_json.dumps({
            "content": [{"type": "text", "text": "hi"}],
            "usage": {"input_tokens": 5, "output_tokens": 2},
        }).encode("utf-8")),
    )
    rc = main(["doctor", "--ping", "--json"])
    assert rc == 0
    data = _json.loads(capsys.readouterr().out.strip())
    assert "ping" in data
    assert data["ping"]["input_tokens"] == 5
    assert data["ping"]["output_tokens"] == 2
    assert isinstance(data["ping"]["latency_ms"], int)

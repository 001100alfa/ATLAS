"""SPEC 030 — atlas run --goal-file A B C batch testleri."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "metrics.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("ATLAS_LLM", "stub")


def _write_ok_goal(path: Path, name: str, filename: str = "kanit.txt") -> None:
    """Başarıyla biten bir static goal (write + file_exists)."""
    path.write_text(
        f"goal: {name}\nplan_kind: static\n"
        f"plan_steps: [\"write:{filename}:ok\"]\n"
        f"action_allowlist: [write]\njudge_kind: file_exists\n"
        f"judge_arg: {filename}\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )


def _write_fail_goal(path: Path, name: str) -> None:
    """Judge asla True dönmez → exit 4 (done=False)."""
    path.write_text(
        f"goal: {name}\nplan_kind: static\n"
        f"plan_steps: [\"write:yok.txt:x\"]\n"
        f"action_allowlist: [write]\njudge_kind: file_exists\n"
        f"judge_arg: hedef-bulunamaz.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )


# ─────────────────────────────────────────────────────────────────────
# Bit-uyumluluk: tek dosya (N=1)
# ─────────────────────────────────────────────────────────────────────


def test_030_tek_dosya_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--goal-file A.yaml` (tek) → 027 davranışı, batch tablosu YOK."""
    _env(monkeypatch, tmp_path)
    y = tmp_path / "solo.yaml"
    _write_ok_goal(y, "tek görev")
    rc = main(["run", "--goal-file", str(y), "--run-id", "solo"])
    assert rc == 0
    out = capsys.readouterr().out
    # Batch başlığı görünmemeli
    assert "ATLAS batch" not in out
    # Tek run kanıtı
    assert (tmp_path / "sb" / "solo-solo" / "kanit.txt").is_file()


# ─────────────────────────────────────────────────────────────────────
# Batch: hepsi başarılı
# ─────────────────────────────────────────────────────────────────────


def test_030_batch_iki_basarili(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """İki başarılı goal → exit 0, özet tablosunda iki done."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "goal A", "a.txt")
    _write_ok_goal(b, "goal B", "b.txt")
    rc = main(["run", "--goal-file", str(a), str(b), "--run-id", "R"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ATLAS batch — 2 goal" in out
    assert "ATLAS batch özeti — 2 goal" in out
    assert out.count("+ done") == 2
    assert "batch exit: 0" in out
    # Run-id suffix
    assert (tmp_path / "sb" / "a-R_1" / "a.txt").is_file()
    assert (tmp_path / "sb" / "b-R_2" / "b.txt").is_file()


# ─────────────────────────────────────────────────────────────────────
# Fail-fast (varsayılan)
# ─────────────────────────────────────────────────────────────────────


def test_030_fail_fast_ilk_hata_kalanlari_atlar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ok, B fail → C atlanır; exit=4."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    c = tmp_path / "c.yaml"
    _write_ok_goal(a, "goal A", "a.txt")
    _write_fail_goal(b, "goal B (fail)")
    _write_ok_goal(c, "goal C", "c.txt")

    rc = main([
        "run", "--goal-file", str(a), str(b), str(c), "--run-id", "R",
    ])
    assert rc == 4
    out = capsys.readouterr().out
    assert "batch exit: 4" in out
    # C atlandı
    assert "atlandı (fail-fast)" in out
    # C çalışmadı → dosya YOK
    assert not (tmp_path / "sb" / "c-R_3" / "c.txt").is_file()


# ─────────────────────────────────────────────────────────────────────
# Continue-on-error
# ─────────────────────────────────────────────────────────────────────


def test_030_continue_on_error_hepsi_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ok, B fail, C ok + --continue-on-error → hepsi çalışır, exit=4."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    c = tmp_path / "c.yaml"
    _write_ok_goal(a, "goal A", "a.txt")
    _write_fail_goal(b, "goal B (fail)")
    _write_ok_goal(c, "goal C", "c.txt")

    rc = main([
        "run", "--goal-file", str(a), str(b), str(c),
        "--run-id", "R", "--continue-on-error",
    ])
    assert rc == 4
    out = capsys.readouterr().out
    # C atlanmadı — dosya var
    assert (tmp_path / "sb" / "c-R_3" / "c.txt").is_file()
    # atlanan işareti YOK
    assert "atlandı" not in out
    # A + C done, B exit=4
    assert out.count("+ done") == 2
    assert "x exit=4" in out


# ─────────────────────────────────────────────────────────────────────
# Exit kodu = max(hata)
# ─────────────────────────────────────────────────────────────────────


def test_030_exit_kodu_en_yuksek(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """B: SPEC HATASI (exit 2), C: done fail (exit 4). continue-on-error → max=4."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b_bozuk.yaml"  # geçersiz YAML
    c = tmp_path / "c.yaml"
    _write_ok_goal(a, "goal A", "a.txt")
    b.write_text("bozuk: içerik: eksik alanlar", encoding="utf-8")  # SpecError → exit 2
    _write_fail_goal(c, "goal C (fail)")

    rc = main([
        "run", "--goal-file", str(a), str(b), str(c),
        "--run-id", "R", "--continue-on-error",
    ])
    # max(0, 2, 4) = 4
    assert rc == 4
    out = capsys.readouterr().out
    assert "batch exit: 4" in out


# ─────────────────────────────────────────────────────────────────────
# Run-id suffix: --run-id verilmediğinde timestamp + _<i>
# ─────────────────────────────────────────────────────────────────────


def test_030_run_id_yok_timestamp_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--run-id` yok → her goal <TS>_<i> run-id alır (aynı TS, farklı i)."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_ok_goal(b, "B", "b.txt")
    rc = main(["run", "--goal-file", str(a), str(b)])
    assert rc == 0
    # Sandbox alt-dizinleri: a-<TS>_1, b-<TS>_2
    sbs = list((tmp_path / "sb").iterdir())
    names = sorted(p.name for p in sbs)
    assert len(names) == 2
    assert names[0].startswith("a-") and names[0].endswith("_1")
    assert names[1].startswith("b-") and names[1].endswith("_2")
    # İkisinin timestamp gövdesi aynı (aynı base_run_id)
    ts_a = names[0].split("a-")[1].rsplit("_", 1)[0]
    ts_b = names[1].split("b-")[1].rsplit("_", 1)[0]
    assert ts_a == ts_b


# ─────────────────────────────────────────────────────────────────────
# Dry-run + batch: hepsine uygulanır
# ─────────────────────────────────────────────────────────────────────


def test_030_dry_run_hepsine_uygulanir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--dry-run + iki dosya → her ikisi de dry-run modunda."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_ok_goal(b, "B", "b.txt")
    rc = main([
        "run", "--goal-file", str(a), str(b), "--dry-run", "--run-id", "DR",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # Her iki goal için "MOD: dry-run" satırı görünür
    assert out.count("dry-run — action yürütme kapalı") == 2
    assert "+ dry-run" in out  # batch mod başlığı


# ─────────────────────────────────────────────────────────────────────
# Boş liste (nargs='+' argparse yakalar → SystemExit 2)
# ─────────────────────────────────────────────────────────────────────


def test_030_bos_liste_argparse_hatasi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--goal-file` sonrası argüman yok → argparse SystemExit 2 fırlatır."""
    _env(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as exc:
        main(["run", "--goal-file"])
    assert exc.value.code == 2


# ═════════════════════════════════════════════════════════════════════
# SPEC 031 — Paralel batch (--jobs N)
# ═════════════════════════════════════════════════════════════════════


def test_031_jobs_1_seri_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--jobs 1` (varsayılan) → mevcut seri davranış (fail-fast)."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_ok_goal(b, "B", "b.txt")
    rc = main(["run", "--goal-file", str(a), str(b), "--run-id", "R"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "mod: fail-fast" in out
    assert "parallel" not in out


def test_031_jobs_2_paralel_iki_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--jobs 2` iki başarılı goal → exit 0, tabloda 2 done."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_ok_goal(b, "B", "b.txt")
    rc = main([
        "run", "--goal-file", str(a), str(b),
        "--run-id", "R", "--jobs", "2",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "parallel (jobs=2)" in out
    assert out.count("+ done") == 2
    assert "batch exit: 0" in out
    # Sandbox path çakışması yok — iki farklı klasör
    assert (tmp_path / "sb" / "a-R_1" / "a.txt").is_file()
    assert (tmp_path / "sb" / "b-R_2" / "b.txt").is_file()


def test_031_paralel_fail_fast_kapali(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--jobs 2` + bir fail → paralel fail-fast anlamsız, tümü çalışır."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    c = tmp_path / "c.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_fail_goal(b, "B (fail)")
    _write_ok_goal(c, "C", "c.txt")
    rc = main([
        "run", "--goal-file", str(a), str(b), str(c),
        "--run-id", "R", "--jobs", "2",
    ])
    assert rc == 4
    out = capsys.readouterr().out
    # C paralel modda ATLANMAZ — hem A hem C tamamlanır
    assert (tmp_path / "sb" / "a-R_1" / "a.txt").is_file()
    assert (tmp_path / "sb" / "c-R_3" / "c.txt").is_file()
    assert "atlandı" not in out
    assert "batch exit: 4" in out


def test_031_paralel_log_karismaz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--jobs 2` çıktı sırası deterministik: [1/N] önce [2/N] sonra."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_ok_goal(b, "B", "b.txt")
    rc = main([
        "run", "--goal-file", str(a), str(b),
        "--run-id", "R", "--jobs", "2",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # [1/2] a önce görünmeli
    i1 = out.find("[1/2] " + str(a))
    i2 = out.find("[2/2] " + str(b))
    assert 0 < i1 < i2
    # Özet en sonda
    isum = out.find("=== ATLAS batch özeti")
    assert i2 < isum


def test_031_jobs_sifir_spec_hatasi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--jobs 0` → SPEC HATASI + exit 2."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_ok_goal(b, "B", "b.txt")
    rc = main([
        "run", "--goal-file", str(a), str(b),
        "--run-id", "R", "--jobs", "0",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--jobs pozitif" in err


def test_031_jobs_5_kucuk_liste(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--jobs 5` ama 2 goal → 2 worker koşar (ThreadPool sınırlar), exit 0."""
    _env(monkeypatch, tmp_path)
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_ok_goal(a, "A", "a.txt")
    _write_ok_goal(b, "B", "b.txt")
    rc = main([
        "run", "--goal-file", str(a), str(b),
        "--run-id", "R", "--jobs", "5",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("+ done") == 2

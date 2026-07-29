"""SPEC 027 — atlas replay testleri."""

from __future__ import annotations

import json
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
    monkeypatch.delenv("ATLAS_LLM_TRACE", raising=False)


def test_027_yaml_kopyasi_olusur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`atlas run --goal-file X` sonrası `.atlas/runs/<goal-id>.yaml` kopyası."""
    _env(monkeypatch, tmp_path)
    y = tmp_path / "gorev.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: static\n"
        "plan_steps: [\"write:kanit.txt:x\"]\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: kanit.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    rc = main(["run", "--goal-file", str(y), "--run-id", "test1"])
    assert rc == 0
    # goal_id = <yaml stem>-<run_id> = gorev-test1
    kopya = tmp_path / "runs" / "gorev-test1.yaml"
    assert kopya.is_file()
    # İçerik birebir
    assert "dosya yaz" in kopya.read_text(encoding="utf-8")


def test_027_replay_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Replay kopyayı bulur ve çalıştırır."""
    _env(monkeypatch, tmp_path)
    y = tmp_path / "gorev.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: static\n"
        "plan_steps: [\"write:kanit.txt:v1\"]\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: kanit.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    main(["run", "--goal-file", str(y), "--run-id", "orig"])

    # Replay — orjinal YAML silinse bile çalışsın
    y.unlink()
    rc = main(["replay", "gorev-orig", "--new-run-id", "replay1"])
    assert rc == 0
    # Yeni sandbox oluşmuş
    replay_sb = tmp_path / "sb" / "gorev-orig-replay1"
    assert (replay_sb / "kanit.txt").is_file()


def test_027_replay_yoksa_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Run-id kopyası yoksa SPEC HATASI + exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["replay", "yok-boyle"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "run bulunamadı: yok-boyle" in err


def test_027_atlas_runs_dir_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ATLAS_RUNS_DIR yol override çalışır."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_RUNS_DIR", str(tmp_path / "custom-runs"))
    y = tmp_path / "gorev.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: static\n"
        "plan_steps: [\"write:x.txt:x\"]\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: x.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    main(["run", "--goal-file", str(y), "--run-id", "ovr"])
    assert (tmp_path / "custom-runs" / "gorev-ovr.yaml").is_file()


def test_027_dashboard_run_id_kolonu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dashboard tablosunda run_id kolonu görünür."""
    _env(monkeypatch, tmp_path)
    y = tmp_path / "gorev.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: static\n"
        "plan_steps: [\"write:x.txt:x\"]\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: x.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    main(["run", "--goal-file", str(y), "--run-id", "dashtest"])

    rc = main(["dashboard"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "run_id" in out
    assert "gorev-dashtest" in out


def test_027_dashboard_json_run_id_alani(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON çıktıda run_id alanı var."""
    _env(monkeypatch, tmp_path)
    y = tmp_path / "gorev.yaml"
    y.write_text(
        "goal: dosya yaz\nplan_kind: static\n"
        "plan_steps: [\"write:x.txt:x\"]\n"
        "action_allowlist: [write]\njudge_kind: file_exists\n"
        "judge_arg: x.txt\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    main(["run", "--goal-file", str(y), "--run-id", "jsontest"])
    # Önceki çıktıyı temizle — dashboard --json sadece kendi çıktısı olsun
    capsys.readouterr()

    rc = main(["dashboard", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["runs"][0]["run_id"] == "gorev-jsontest"

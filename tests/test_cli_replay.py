"""SPEC 027 + 028 — atlas replay testleri."""

from __future__ import annotations

import json
import os
import time
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


# ─────────────────────────────────────────────────────────────────────────────
# SPEC 028 — atlas replay --list
# ─────────────────────────────────────────────────────────────────────────────


def _write_run_yaml(runs_dir: Path, run_id: str, goal: str, mtime: float | None = None) -> Path:
    """Test yardımcısı: `.atlas/runs/<run_id>.yaml` yaz + opsiyonel mtime."""
    runs_dir.mkdir(parents=True, exist_ok=True)
    p = runs_dir / f"{run_id}.yaml"
    p.write_text(
        f"goal: {goal}\nplan_kind: static\nplan_steps: []\n"
        "action_allowlist: []\njudge_kind: file_exists\n"
        "judge_arg: x\nbudget: 20\nmax_steps: 2\n",
        encoding="utf-8",
    )
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def test_028_list_bos_klasor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas replay --list` klasör yoksa `(hiç kayıt yok)` + exit 0."""
    _env(monkeypatch, tmp_path)
    rc = main(["replay", "--list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(hiç kayıt yok)" in out


def test_028_list_mtime_desc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """İki run: en yeni önce, run_id ve goal görünür."""
    _env(monkeypatch, tmp_path)
    runs_dir = tmp_path / "runs"
    now = time.time()
    _write_run_yaml(runs_dir, "eski", "eski hedef metni", mtime=now - 3600)
    _write_run_yaml(runs_dir, "yeni", "yeni hedef metni", mtime=now)

    rc = main(["replay", "--list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "yeni" in out
    assert "eski" in out
    assert "yeni hedef metni" in out
    # Sıra: en yeni önce
    assert out.index("yeni") < out.index("eski")


def test_028_list_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--list --json` JSON liste basar; alanlar: run_id, mtime, goal."""
    _env(monkeypatch, tmp_path)
    runs_dir = tmp_path / "runs"
    _write_run_yaml(runs_dir, "tek", "test hedefi")

    rc = main(["replay", "--list", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["run_id"] == "tek"
    assert data[0]["goal"] == "test hedefi"
    assert "mtime" in data[0]


def test_028_list_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--list --limit 2` en yeni iki kaydı verir."""
    _env(monkeypatch, tmp_path)
    runs_dir = tmp_path / "runs"
    now = time.time()
    _write_run_yaml(runs_dir, "r1", "hedef 1", mtime=now - 300)
    _write_run_yaml(runs_dir, "r2", "hedef 2", mtime=now - 200)
    _write_run_yaml(runs_dir, "r3", "hedef 3", mtime=now - 100)

    rc = main(["replay", "--list", "--limit", "2", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert len(data) == 2
    assert {r["run_id"] for r in data} == {"r2", "r3"}


def test_028_list_yaml_disi_yoksay(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`.txt` gibi yaml-dışı dosyalar listeye girmez."""
    _env(monkeypatch, tmp_path)
    runs_dir = tmp_path / "runs"
    _write_run_yaml(runs_dir, "gecerli", "gerçek run")
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "not.txt").write_text("çöp", encoding="utf-8")
    (runs_dir / "eski.yml").write_text("goal: yml uzantısı\n", encoding="utf-8")

    rc = main(["replay", "--list", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    ids = {r["run_id"] for r in data}
    assert ids == {"gecerli"}


def test_028_replay_arg_hatasi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas replay` (run-id yok, --list yok) → SPEC HATASI + exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["replay"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "run-id ya da --list gerekli" in err


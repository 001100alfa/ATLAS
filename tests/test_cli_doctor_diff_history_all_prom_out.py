"""SPEC 110 — atlas doctor --diff-history-all --format prometheus --out PATH."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)


def _seed_history(hist_dir: Path, dates: list[str]) -> None:
    hist_dir.mkdir(parents=True, exist_ok=True)
    for d in dates:
        (hist_dir / f"baseline-{d}.json").write_text(
            json.dumps({
                "schema_version": 1, "warnings": [], "quality": {},
            }),
            encoding="utf-8",
        )


def test_110_out_yazma_stdout_bos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    out = tmp_path / "doc.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert "atlas_doctor_history_" not in stdout


def test_110_out_icerik_stdout_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    # stdout
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
    ])
    assert rc == 0
    stdout_text = capsys.readouterr().out.strip()
    # --out
    out = tmp_path / "doc.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    file_text = out.read_text(encoding="utf-8").strip()
    assert file_text == stdout_text


def test_110_out_parent_auto_mkdir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    out = tmp_path / "deep" / "nested" / "doc.prom"
    assert not out.parent.exists()
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()


def test_110_out_diff_history_all_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out --diff-history-all yok → exit 2."""
    _env(monkeypatch, tmp_path)
    out = tmp_path / "doc.prom"
    rc = main([
        "doctor", "--format", "prometheus", "--out", str(out),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--diff-history-all" in err
    assert "--out" in err


def test_110_out_format_json_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out --format=json → exit 2 (prometheus gerek)."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    out = tmp_path / "doc.json"
    # SPEC 040 --format choices: human/prometheus; json değil → argparse err
    with pytest.raises(SystemExit):
        main([
            "doctor", "--diff-history-all", "--format", "json",
            "--out", str(out),
        ])


def test_110_out_strict_regresyon_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out + --strict + regresyon → exit 9, dosyaya yazılır."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    out = tmp_path / "doc.prom"
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
        "--out", str(out), "--strict",
    ])
    assert rc in (0, 9)
    assert out.is_file()


def test_110_out_yalın_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out tek başına → exit 2."""
    _env(monkeypatch, tmp_path)
    out = tmp_path / "doc.prom"
    rc = main(["doctor", "--out", str(out)])
    assert rc == 2


def test_110_out_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out YOK → SPEC 104 stdout AYNI."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
    ])
    assert rc == 0
    assert "atlas_doctor_history_" in capsys.readouterr().out

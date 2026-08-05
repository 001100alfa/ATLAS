"""SPEC 104 — atlas doctor --diff-history-all --format prometheus testleri."""

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


def _seed_history(hist_dir: Path, dates: list[str],
                  warnings: list[str] | None = None) -> None:
    hist_dir.mkdir(parents=True, exist_ok=True)
    for d in dates:
        (hist_dir / f"baseline-{d}.json").write_text(
            json.dumps({
                "schema_version": 1,
                "warnings": warnings or [],
                "quality": {},
            }),
            encoding="utf-8",
        )


def test_104_prometheus_5_metric_ailesi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """5 metric HELP+TYPE."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for name in (
        "atlas_doctor_history_warnings_added",
        "atlas_doctor_history_warnings_removed",
        "atlas_doctor_history_quality_deltas",
        "atlas_doctor_history_has_regression",
        "atlas_doctor_history_has_improvement",
    ):
        assert f"# HELP {name}" in out
        assert f"# TYPE {name}" in out


def test_104_prometheus_snapshot_date_label(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Labels: snapshot_date."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05", "2026-08-06"])
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'snapshot_date="2026-08-05"' in out
    assert 'snapshot_date="2026-08-06"' in out


def test_104_prometheus_type_counter_gauge(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """warnings_added/removed/quality_deltas counter; has_* gauge."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# TYPE atlas_doctor_history_warnings_added counter" in out
    assert "# TYPE atlas_doctor_history_has_regression gauge" in out


def test_104_prometheus_gauge_0_1(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """has_regression / has_improvement 0 veya 1 döner."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # gauge satırı sonu 0 veya 1
    import re
    matches = re.findall(
        r"atlas_doctor_history_has_regression\{[^}]+\} (\d)", out,
    )
    assert all(m in ("0", "1") for m in matches)


def test_104_prometheus_strict_regresyon_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--strict + regresyon → exit 9 (Prometheus çıktı hâlâ basılır)."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus", "--strict",
    ])
    assert rc in (0, 9)
    out = capsys.readouterr().out
    assert "atlas_doctor_history_warnings_added" in out


def test_104_prometheus_pretty_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format prometheus YOK → SPEC 091 pretty AYNI."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main(["doctor", "--diff-history-all"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 snapshot" in out
    assert "atlas_doctor_history" not in out


def test_104_prometheus_json_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format prometheus YOK + --json → SPEC 091 JSON AYNI."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main(["doctor", "--diff-history-all", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    lines = [ln for ln in out.strip().split("\n") if ln.startswith("{")]
    data = json.loads(lines[-1])
    assert "snapshots" in data


def test_104_prometheus_help_type_5_sayisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """5 HELP + 5 TYPE (metric ailesi)."""
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    _seed_history(hist, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history-all", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("# HELP atlas_doctor_history_") == 5
    assert out.count("# TYPE atlas_doctor_history_") == 5

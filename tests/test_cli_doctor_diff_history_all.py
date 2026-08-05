"""SPEC 091 — atlas doctor --diff-history-all testleri."""

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


def _seed_history(tmp_path: Path, dates: list[str]) -> Path:
    hist = tmp_path / ".atlas" / "doctor-history"
    hist.mkdir(parents=True, exist_ok=True)
    skeleton = {
        "schema_version": 1,
        "warnings": [],
        "quality": {},
    }
    for d in dates:
        (hist / f"baseline-{d}.json").write_text(
            json.dumps(skeleton), encoding="utf-8",
        )
    return hist


def test_091_diff_history_all_bos_tarihce_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--diff-history-all"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "tarihçe" in err or "tarihce" in err


def test_091_diff_history_all_tum_snapshotlar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """3 snapshot → tablo 3 satır + date desc."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-06-01", "2026-08-05", "2026-07-15"])
    rc = main(["doctor", "--diff-history-all"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "3 snapshot" in out
    # date desc
    lines = out.split("\n")
    # tablo satırlarını bul (date başlar)
    date_lines = [ln for ln in lines if ln.strip().startswith("2026-")]
    dates = [ln.split()[0] for ln in date_lines]
    assert dates == ["2026-08-05", "2026-07-15", "2026-06-01"]


def test_091_diff_history_all_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json → snapshots listesi + her delta SPEC 057 anahtarları."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05", "2026-08-01"])
    rc = main(["doctor", "--diff-history-all", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    # JSON son satırda
    lines = [ln for ln in out.strip().split("\n") if ln.startswith("{")]
    data = json.loads(lines[-1])
    assert "snapshots" in data
    assert len(data["snapshots"]) == 2
    for s in data["snapshots"]:
        assert "date" in s
        assert "path" in s
        assert "warnings_added" in s["delta"]
        assert "warnings_removed" in s["delta"]


def test_091_diff_history_all_diff_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history-all + --diff → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    other = tmp_path / "o.json"
    other.write_text(
        '{"schema_version":1,"warnings":[],"quality":{}}',
        encoding="utf-8",
    )
    rc = main(["doctor", "--diff-history-all", "--diff", str(other)])
    assert rc == 2


def test_091_diff_history_all_diff_history_n_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history-all + --diff-history N → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main(["doctor", "--diff-history-all", "--diff-history", "1"])
    assert rc == 2


def test_091_diff_history_all_save_baseline_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history-all + --save-baseline → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main(["doctor", "--diff-history-all", "--save-baseline"])
    assert rc == 2


def test_091_diff_history_all_auto_baseline_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    (tmp_path / ".atlas" / "doctor-baseline.json").write_text(
        '{"schema_version":1,"warnings":[],"quality":{}}',
        encoding="utf-8",
    )
    rc = main(["doctor", "--diff-history-all", "--auto-baseline"])
    assert rc == 2


def test_091_diff_history_all_schema_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--schema` SPEC 040 kısa devre → `--diff-history-all` ignored,
    şema JSON basılır (SPEC 040 kalıbı BİT-UYUMLU)."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main(["doctor", "--diff-history-all", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"


def test_091_104_diff_history_all_prometheus_no_longer_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SPEC 104: --diff-history-all + --format prometheus MUTEX kaldırıldı,
    artık per-snapshot metric ailesi yayımlanır."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main(["doctor", "--diff-history-all", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_doctor_history_warnings_added" in out


def test_091_diff_history_all_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history-all YOK → SPEC 021 doctor çıktısı AYNI."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main(["doctor"])
    assert rc in (0, 9)
    out = capsys.readouterr().out
    assert "diff-history-all" not in out

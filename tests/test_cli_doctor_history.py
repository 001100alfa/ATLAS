"""SPEC 080 — atlas doctor --save-baseline history + --history-list."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import (
    _DEFAULT_DOCTOR_HISTORY_DIR,
    _list_doctor_history,
    _prune_doctor_history,
    main,
)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)


# ═════════════════════════════════════════════════════════════════════
# _list_doctor_history + _prune_doctor_history (birim)
# ═════════════════════════════════════════════════════════════════════


def test_080_list_history_dizin_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    assert _list_doctor_history() == []


def test_080_list_history_bos_dizin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    _DEFAULT_DOCTOR_HISTORY_DIR.mkdir(parents=True)
    assert _list_doctor_history() == []


def test_080_list_history_snapshot_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    _DEFAULT_DOCTOR_HISTORY_DIR.mkdir(parents=True)
    (_DEFAULT_DOCTOR_HISTORY_DIR / "baseline-2026-08-05.json").write_text(
        '{"x": 1}', encoding="utf-8",
    )
    entries = _list_doctor_history()
    assert len(entries) == 1
    assert entries[0]["date"] == "2026-08-05"
    assert entries[0]["size_bytes"] > 0


def test_080_list_history_date_desc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    _DEFAULT_DOCTOR_HISTORY_DIR.mkdir(parents=True)
    for d in ("2026-06-01", "2026-08-05", "2026-07-15"):
        (_DEFAULT_DOCTOR_HISTORY_DIR / f"baseline-{d}.json").write_text(
            "{}", encoding="utf-8",
        )
    entries = _list_doctor_history()
    assert [e["date"] for e in entries] == [
        "2026-08-05", "2026-07-15", "2026-06-01",
    ]


def test_080_prune_history_keep_1(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    _DEFAULT_DOCTOR_HISTORY_DIR.mkdir(parents=True)
    for d in ("2026-01-01", "2026-06-01", "2026-08-05"):
        (_DEFAULT_DOCTOR_HISTORY_DIR / f"baseline-{d}.json").write_text(
            "{}", encoding="utf-8",
        )
    deleted = _prune_doctor_history(1)
    assert len(deleted) == 2
    remaining = list(_DEFAULT_DOCTOR_HISTORY_DIR.glob("baseline-*.json"))
    assert len(remaining) == 1
    assert remaining[0].name == "baseline-2026-08-05.json"


def test_080_prune_history_keep_sifir_hata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match=">= 1"):
        _prune_doctor_history(0)


# ═════════════════════════════════════════════════════════════════════
# CLI: --save-baseline history yan etki + --history-keep + --history-list
# ═════════════════════════════════════════════════════════════════════


def test_080_cli_save_baseline_default_history_kopyasi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--save-baseline` (default path) → default JSON + tarihçe snapshot."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--save-baseline"])
    assert rc == 0
    default = tmp_path / ".atlas" / "doctor-baseline.json"
    assert default.is_file()
    # Tarihçe snapshot da yazılmış (bugünün tarihiyle)
    history_files = list(
        (tmp_path / ".atlas" / "doctor-history").glob("baseline-*.json")
    )
    assert len(history_files) == 1
    # İçerik aynı
    assert default.read_text() == history_files[0].read_text()
    out = capsys.readouterr().out
    assert "tarihce snapshot" in out


def test_080_cli_save_baseline_custom_path_history_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Custom `--save-baseline PATH` → tarihçe kopyası YOK (custom = bilinçli)."""
    _env(monkeypatch, tmp_path)
    custom = tmp_path / "snapshots" / "prod.json"
    rc = main(["doctor", "--save-baseline", str(custom)])
    assert rc == 0
    assert custom.is_file()
    # .atlas/doctor-history/ oluşmadı
    hist_dir = tmp_path / ".atlas" / "doctor-history"
    assert not hist_dir.exists() or not list(hist_dir.glob("*.json"))


def test_080_cli_history_keep_retention(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Mevcut 3 eski history + save + --history-keep 2 → 2 kalır."""
    _env(monkeypatch, tmp_path)
    hist_dir = tmp_path / ".atlas" / "doctor-history"
    hist_dir.mkdir(parents=True)
    # Bugünden eski 3 snapshot
    for d in ("2024-01-01", "2024-02-01", "2024-03-01"):
        (hist_dir / f"baseline-{d}.json").write_text("{}", encoding="utf-8")
    rc = main(["doctor", "--save-baseline", "--history-keep", "2"])
    assert rc == 0
    remaining = sorted(f.name for f in hist_dir.glob("baseline-*.json"))
    # Bugünün snapshot + en yeni eski (2024-03-01) kalır (2)
    assert len(remaining) == 2
    assert "baseline-2024-03-01.json" in remaining


def test_080_cli_history_keep_sifir_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--save-baseline", "--history-keep", "0"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--history-keep" in err


def test_080_cli_history_list_bos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--history-list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "0 snapshot" in out or "(snapshot yok)" in out


def test_080_cli_history_list_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    hist = tmp_path / ".atlas" / "doctor-history"
    hist.mkdir(parents=True)
    (hist / "baseline-2026-08-05.json").write_text("{}", encoding="utf-8")
    rc = main(["doctor", "--history-list", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["date"] == "2026-08-05"


def test_080_cli_history_list_saglik_kontrolu_yapmaz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--history-list kısa devre — doctor sağlık kontrolü YAPMAZ."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--history-list"])
    assert rc == 0
    out = capsys.readouterr().out
    # SPEC 021 doctor sağlık başlığı GÖRÜNMEZ
    assert "ATLAS doctor — env sağlık" not in out


def test_080_cli_save_baseline_bit_uyumlu_yoksa(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Yalnız --save-baseline (history-keep yok) → default davranış +
    otomatik tarihçe (yeni SPEC 080; bit-uyumluluk: tarihçe yan etki)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--save-baseline"])
    assert rc == 0
    default = tmp_path / ".atlas" / "doctor-baseline.json"
    assert default.is_file()
    # SPEC 080: her save default'ta tarihçe kopyalanır
    hist_files = list(
        (tmp_path / ".atlas" / "doctor-history").glob("baseline-*.json")
    )
    assert len(hist_files) == 1

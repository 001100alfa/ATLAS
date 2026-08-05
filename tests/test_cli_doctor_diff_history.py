"""SPEC 086 — atlas doctor --diff-history N testleri."""

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
    """`.atlas/doctor-history/baseline-<date>.json` boş rapor iskeleti yaz."""
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


def test_086_diff_history_bos_tarihce_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Tarihçe boş → SPEC HATASI exit 2 + öneri."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--diff-history", "1"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "tarihçe" in err or "tarihce" in err
    assert "--save-baseline" in err


def test_086_diff_history_negatif_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """N < 1 → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-01"])
    rc = main(["doctor", "--diff-history", "0"])
    assert rc == 2
    assert "--diff-history" in capsys.readouterr().err


def test_086_diff_history_asan_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """N > len → SPEC HATASI exit 2 (len mesajda)."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-01", "2026-08-02"])
    rc = main(["doctor", "--diff-history", "5"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "5" in err
    assert "2" in err  # len


def test_086_diff_history_n1_en_yeni(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """N=1 → en yeni snapshot; diff çalışır (rc==0)."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-01", "2026-08-05"])
    rc = main(["doctor", "--diff-history", "1"])
    # Diff başarılı çalışır: rc 0 veya 9 (strict yok → 0)
    assert rc == 0
    out = capsys.readouterr().out
    # snapshot seçildi mesajı
    assert "diff-history" in out
    assert "2026-08-05" in out  # en yeni


def test_086_diff_history_n_max_en_eski(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """N=len → en eski snapshot."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-01", "2026-08-05"])
    rc = main(["doctor", "--diff-history", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "2026-08-01" in out  # en eski (N=2/2)


def test_086_diff_history_diff_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history + --diff → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    other = tmp_path / "other.json"
    other.write_text('{"schema_version":1,"warnings":[],"quality":{}}',
                     encoding="utf-8")
    rc = main([
        "doctor", "--diff-history", "1", "--diff", str(other),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MUTEX" in err or "birlikte kullanılamaz" in err


def test_086_diff_history_auto_baseline_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history + --auto-baseline → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    # auto-baseline default baseline dosyası da olsun (aksi hâlde early
    # return 0)
    (tmp_path / ".atlas" / "doctor-baseline.json").write_text(
        '{"schema_version":1,"warnings":[],"quality":{}}',
        encoding="utf-8",
    )
    rc = main([
        "doctor", "--diff-history", "1", "--auto-baseline",
    ])
    assert rc == 2


def test_086_diff_history_save_baseline_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history + --save-baseline → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history", "1", "--save-baseline",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MUTEX" in err or "birlikte kullanılamaz" in err


def test_086_diff_history_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history --json → SPEC 057 delta şeması bit-uyumlu."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main([
        "doctor", "--diff-history", "1", "--json",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # snapshot mesajı stdout'a gitmiş olabilir; JSON son satırda
    lines = [ln for ln in out.strip().split("\n") if ln.startswith("{")]
    assert len(lines) >= 1
    data = json.loads(lines[-1])
    # SPEC 057 delta anahtarları
    assert "warnings_added" in data
    assert "warnings_removed" in data


def test_086_diff_history_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff-history VERİLMEZSE mevcut doctor çıktısı AYNI (SPEC 021)."""
    _env(monkeypatch, tmp_path)
    _seed_history(tmp_path, ["2026-08-05"])
    rc = main(["doctor"])
    assert rc in (0, 9)  # sağlık kontrolüne bağlı, ama rc değişmez
    out = capsys.readouterr().out
    # diff mesajı YOK
    assert "diff-history" not in out

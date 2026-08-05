"""SPEC 062 — atlas doctor --auto-baseline + --save-baseline testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import _DEFAULT_DOCTOR_BASELINE, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)


def test_062_default_baseline_path_sabit() -> None:
    """`.atlas/doctor-baseline.json` sabit yol."""
    assert _DEFAULT_DOCTOR_BASELINE == Path(".atlas/doctor-baseline.json")


# ═════════════════════════════════════════════════════════════════════
# --save-baseline
# ═════════════════════════════════════════════════════════════════════


def test_062_save_baseline_default_yol(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--save-baseline` bayraksız → .atlas/doctor-baseline.json'a yazar."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--save-baseline"])
    assert rc == 0
    default = tmp_path / ".atlas" / "doctor-baseline.json"
    assert default.is_file()
    data = json.loads(default.read_text(encoding="utf-8"))
    # Zorunlu doctor alanları var (bit-uyumlu)
    assert "warnings" in data
    assert "quality" in data
    out = capsys.readouterr().out
    assert "baseline yazıldı" in out


def test_062_save_baseline_custom_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--save-baseline PATH` → verilen yola yazar; dizini oluşturur."""
    _env(monkeypatch, tmp_path)
    custom = tmp_path / "snapshots" / "gate.json"
    rc = main(["doctor", "--save-baseline", str(custom)])
    assert rc == 0
    assert custom.is_file()
    data = json.loads(custom.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_062_save_baseline_diff_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--save-baseline` + `--diff` semantik hata (exit 2)."""
    _env(monkeypatch, tmp_path)
    other = tmp_path / "other.json"
    other.write_text('{"warnings": []}', encoding="utf-8")
    rc = main(["doctor", "--save-baseline", "--diff", str(other)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--save-baseline ile --diff" in err


def test_062_save_baseline_auto_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--save-baseline", "--auto-baseline"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--save-baseline ile --diff/--auto-baseline" in err


def test_062_save_baseline_format_prometheus_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main([
        "doctor", "--save-baseline", "--format", "prometheus",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--save-baseline ile --format prometheus" in err


# ═════════════════════════════════════════════════════════════════════
# --auto-baseline
# ═════════════════════════════════════════════════════════════════════


def test_062_auto_baseline_ilk_calistirma_nazik(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Baseline yoksa: bilgi + exit 0 (ilk çalıştırma nazikliği)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--auto-baseline"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "baseline yok" in out
    assert "--save-baseline" in out


def test_062_auto_baseline_diff_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Save + auto: aynı raporla karşılaştırma → değişiklik yok."""
    _env(monkeypatch, tmp_path)
    # 1) Save baseline
    rc1 = main(["doctor", "--save-baseline"])
    assert rc1 == 0
    capsys.readouterr()  # temizle
    # 2) Auto-baseline diff — kendi kendine karşılaştırma
    rc2 = main(["doctor", "--auto-baseline"])
    assert rc2 == 0
    out = capsys.readouterr().out
    assert "=== ATLAS doctor --diff" in out
    assert "OK degisiklik yok" in out


def test_062_auto_baseline_diff_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--auto-baseline` + `--diff` semantik hata."""
    _env(monkeypatch, tmp_path)
    other = tmp_path / "explicit.json"
    other.write_text('{"warnings": []}', encoding="utf-8")
    rc = main(["doctor", "--auto-baseline", "--diff", str(other)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--auto-baseline ile --diff" in err


def test_062_auto_baseline_strict_regresyon_exit_9(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Save + değişiklik + strict + auto → regresyon exit 9."""
    _env(monkeypatch, tmp_path)
    # 1) İlk save: vault yok (varsayılan warning)
    rc1 = main(["doctor", "--save-baseline"])
    assert rc1 == 0
    capsys.readouterr()
    # 2) Baseline'ı bozacak şekilde manipüle et — baseline'a warning yok olarak yaz
    baseline = tmp_path / ".atlas" / "doctor-baseline.json"
    data = json.loads(baseline.read_text(encoding="utf-8"))
    # Baseline'da vault_health warning None yap (mevcut current warning
    # olarak regressed dönmesi için)
    if "quality" in data and "vault_health" in data["quality"]:
        data["quality"]["vault_health"]["warning"] = None
    baseline.write_text(json.dumps(data), encoding="utf-8")
    # 3) auto-baseline + strict → regresyon = exit 9
    rc = main(["doctor", "--auto-baseline", "--strict"])
    assert rc == 9
    err = capsys.readouterr().err
    assert "REGRESYON" in err


def test_062_default_doctor_calistirma_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--save-baseline / --auto-baseline YOKSA default doctor davranışı."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS doctor" in out
    assert "baseline yazıldı" not in out

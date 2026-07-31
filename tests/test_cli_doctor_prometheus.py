"""SPEC 047 — atlas doctor --format prometheus testleri."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import _doctor_report_to_prometheus, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Doctor kalite kapılarını temiz tutmak için env izolasyonu."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)


# ═════════════════════════════════════════════════════════════════════
# _doctor_report_to_prometheus (birim)
# ═════════════════════════════════════════════════════════════════════


def test_047_prometheus_up_ve_warnings_zorunlu() -> None:
    """`atlas_doctor_up 1` ve `warnings_total` her raporda basılır."""
    report = {"warnings": [], "quality": {}}
    text = _doctor_report_to_prometheus(report)
    assert "# TYPE atlas_doctor_up gauge" in text
    assert "atlas_doctor_up 1" in text
    assert "# TYPE atlas_doctor_warnings_total gauge" in text
    assert "atlas_doctor_warnings_total 0" in text


def test_047_prometheus_warnings_sayilir() -> None:
    """`warnings` listesi uzunluğu counter değeri olur."""
    report = {"warnings": ["a", "b", "c"], "quality": {}}
    text = _doctor_report_to_prometheus(report)
    assert "atlas_doctor_warnings_total 3" in text


def test_047_prometheus_quality_label_healthy() -> None:
    """Quality alanı warning=None → healthy=1; warning var → healthy=0."""
    report = {
        "warnings": [],
        "quality": {
            "decisions_drift": {"warning": None, "last_date": "2026-07-31"},
            "vault_health": {"warning": "vault boş", "notes_total": 0},
            "entry_count": {"warning": None},
        },
    }
    text = _doctor_report_to_prometheus(report)
    assert '# TYPE atlas_doctor_quality_healthy gauge' in text
    assert 'atlas_doctor_quality_healthy{field="decisions_drift"} 1' in text
    assert 'atlas_doctor_quality_healthy{field="vault_health"} 0' in text
    assert 'atlas_doctor_quality_healthy{field="entry_count"} 1' in text


def test_047_prometheus_scan_src_metrikleri_kosullu() -> None:
    """scan_src alanı yoksa detay metrikleri BASILMAZ."""
    report = {"warnings": [], "quality": {"vault_health": {"warning": None}}}
    text = _doctor_report_to_prometheus(report)
    assert "atlas_doctor_scan_src_hits_total" not in text
    assert "atlas_doctor_scan_src_unique_files" not in text


def test_047_prometheus_scan_src_metrikleri_dolu() -> None:
    """scan_src alanı varsa detay metrikleri (hits + unique) basılır."""
    report = {
        "warnings": [],
        "quality": {
            "scan_src": {
                "warning": None,
                "total": 3,
                "unique_hits": 2,
                "sample_files": ["a.py", "b.py"],
            }
        },
    }
    text = _doctor_report_to_prometheus(report)
    assert "atlas_doctor_scan_src_hits_total 3" in text
    assert "atlas_doctor_scan_src_unique_files 2" in text


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas doctor --format prometheus
# ═════════════════════════════════════════════════════════════════════


def test_047_cli_doctor_format_prometheus_temel_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas doctor --format prometheus` → text çıktı; up + warnings + quality."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # Zorunlu metrikler
    assert "atlas_doctor_up 1" in out
    assert "atlas_doctor_warnings_total" in out
    # HELP + TYPE satırları
    assert "# HELP atlas_doctor_up" in out
    assert "# TYPE atlas_doctor_up gauge" in out
    # Quality label(lar)ı — en az bir alan bekleniyor
    assert 'atlas_doctor_quality_healthy{field=' in out


def test_047_cli_doctor_format_prometheus_json_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json --format prometheus` argparse mutex → SystemExit(2)."""
    _env(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["doctor", "--json", "--format", "prometheus"])
    assert excinfo.value.code == 2


def test_047_cli_doctor_format_prometheus_schema_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--schema --format prometheus` argparse mutex → SystemExit(2)."""
    _env(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["doctor", "--schema", "--format", "prometheus"])
    assert excinfo.value.code == 2


def test_047_cli_doctor_json_schema_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`--json --schema` da mutex (yeni add_mutually_exclusive_group)."""
    _env(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["doctor", "--json", "--schema"])
    assert excinfo.value.code == 2


def test_047_cli_doctor_default_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default (bayraksız) çıktı: SPEC 021 insan formatı KORUNUR."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS doctor" in out
    assert "atlas_doctor_" not in out  # Prometheus sızmasın


def test_047_cli_doctor_format_human_default_davranis(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--format human` = default davranış (bit-uyumlu)."""
    _env(monkeypatch, tmp_path)
    rc = main(["doctor", "--format", "human"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS doctor" in out
    assert "atlas_doctor_" not in out

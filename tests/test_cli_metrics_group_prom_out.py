"""SPEC 096 — atlas metrics --group-by --format prometheus --out PATH testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return metrics


def _write_metrics(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


def test_096_out_yazma_stdout_bos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out PATH → dosya, stdout Prometheus text basmaz."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 100}])
    out = tmp_path / "metrics.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert "atlas_metrics_group_records" not in stdout
    # Dosyada içerik var
    text = out.read_text(encoding="utf-8")
    assert "atlas_metrics_group_records" in text


def test_096_out_icerik_stdout_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dosya içeriği stdout modu ile AYNI."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100, "out": 50},
    ])
    # 1. stdout
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
    ])
    assert rc == 0
    stdout_text = capsys.readouterr().out.strip()
    # 2. --out
    out = tmp_path / "sub" / "m.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    file_text = out.read_text(encoding="utf-8").strip()
    assert file_text == stdout_text


def test_096_out_parent_dir_auto_mkdir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parent dizin auto-mkdir."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    out = tmp_path / "deep" / "nested" / "m.prom"
    assert not out.parent.exists()
    rc = main([
        "metrics", "--group-by", "day", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()


def test_096_out_yazma_hatasi_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PATH mevcut dizinse → write_text başarısız → exit 2."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    target_dir = tmp_path / "as_dir"
    target_dir.mkdir()
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
        "--out", str(target_dir),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err or "yazıl" in err


def test_096_out_group_by_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out --format prometheus (group-by yok) → exit 2."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--format", "prometheus",
        "--out", str(out),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--group-by" in err
    assert "--out" in err


def test_096_out_format_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out --group-by (format yok) → exit 2."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "hour",
        "--out", str(out),
    ])
    assert rc == 2


def test_096_out_yalın_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out tek başına → exit 2."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "2026-08-05T14:00:00", "in": 1}])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--out", str(out),
    ])
    assert rc == 2


def test_096_out_with_cost_ile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out + --with-cost → dosyada cost_usd metric var."""
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 1_000_000, "out": 500_000},
    ])
    out = tmp_path / "m.prom"
    rc = main([
        "metrics", "--group-by", "hour", "--with-cost",
        "--format", "prometheus", "--out", str(out),
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "atlas_metrics_group_cost_usd" in text
    assert "10.500000" in text


def test_096_out_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out YOK → SPEC 090 stdout AYNI."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2026-08-05T14:00:00", "in": 100},
    ])
    rc = main([
        "metrics", "--group-by", "hour", "--format", "prometheus",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_group_records" in out

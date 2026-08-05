"""SPEC 076 — atlas metrics --window MINUTES testleri."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from atlas_core.cli import _filter_records_by_window, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return metrics


def _write_metrics(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


# ═════════════════════════════════════════════════════════════════════
# _filter_records_by_window (birim)
# ═════════════════════════════════════════════════════════════════════


def test_076_window_none_filtreleme_yok() -> None:
    """`window_minutes=None` → orijinal liste."""
    recs = [{"ts": "2026-08-05T10:00:00", "in": 1}]
    assert _filter_records_by_window(recs, None) is recs


def test_076_window_5_dk_eski_kayit_atilir() -> None:
    """5 dk pencere: 10 dk önceki kayıt atılır, 2 dk önceki tutulur."""
    now = datetime(2026, 8, 5, 12, 0, 0)
    recs = [
        {"ts": (now - timedelta(minutes=10)).isoformat(timespec="seconds"),
         "in": 1, "id": "eski"},
        {"ts": (now - timedelta(minutes=2)).isoformat(timespec="seconds"),
         "in": 2, "id": "yeni"},
    ]
    out = _filter_records_by_window(recs, 5.0, now=now)
    assert len(out) == 1
    assert out[0]["id"] == "yeni"


def test_076_window_hepsi_yeni_hepsi_dahil() -> None:
    now = datetime(2026, 8, 5, 12, 0, 0)
    recs = [
        {"ts": (now - timedelta(seconds=30)).isoformat(timespec="seconds"),
         "in": 1},
        {"ts": (now - timedelta(seconds=60)).isoformat(timespec="seconds"),
         "in": 2},
    ]
    out = _filter_records_by_window(recs, 5.0, now=now)
    assert len(out) == 2


def test_076_window_ts_yok_kayit_nazik_dahil() -> None:
    """`ts` alanı olmayan kayıt filtre içi (defensive)."""
    now = datetime(2026, 8, 5, 12, 0, 0)
    recs = [
        {"in": 1},  # ts yok
        {"ts": "not-iso", "in": 2},  # parse edilemez
        {"ts": (now - timedelta(minutes=1)).isoformat(timespec="seconds"),
         "in": 3},
    ]
    out = _filter_records_by_window(recs, 5.0, now=now)
    assert len(out) == 3  # üçü de dahil (nazik)


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas metrics --window
# ═════════════════════════════════════════════════════════════════════


def test_076_cli_window_filtresi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--window 5 → sadece son 5 dk kayıt sayılır."""
    now = datetime.now()
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        # 10 dk önceki (window dışı)
        {"ts": (now - timedelta(minutes=10)).isoformat(timespec="seconds"),
         "in": 100, "out": 50, "cache_c": 0, "cache_r": 0},
        # 2 dk önceki (window içi)
        {"ts": (now - timedelta(minutes=2)).isoformat(timespec="seconds"),
         "in": 200, "out": 100, "cache_c": 0, "cache_r": 0},
    ])
    rc = main(["metrics", "--window", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 1 çağrı" in out
    assert "input tokens:   200" in out


def test_076_cli_window_gecersiz_deger_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--window <= 0 → exit 2 SPEC HATASI."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--window", "0"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_076_cli_window_negatif_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--window", "-3"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--window > 0" in err


def test_076_cli_window_limit_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--window + --limit birlikte: önce window sonra son N limit."""
    now = datetime.now()
    metrics = _env(monkeypatch, tmp_path)
    # 5 kayıt hepsi son 5 dk içinde; --window 5 hepsi geçer; --limit 2
    # sadece son 2'yi tutar
    _write_metrics(metrics, [
        {"ts": (now - timedelta(minutes=i)).isoformat(timespec="seconds"),
         "in": i * 10, "out": i, "cache_c": 0, "cache_r": 0}
        for i in range(4, -1, -1)  # 4,3,2,1,0 dk önce
    ])
    rc = main(["metrics", "--window", "5", "--limit", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 2 çağrı" in out


def test_076_cli_window_bit_uyumlu_yoksa(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--window yoksa mevcut davranış bit-uyumlu."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "2020-01-01T00:00:00", "in": 100, "out": 50},
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 1 çağrı" in out  # eski kayıt yine sayılır (window YOK)


def test_076_cli_window_json_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--window + --json birlikte çalışır."""
    now = datetime.now()
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": (now - timedelta(minutes=1)).isoformat(timespec="seconds"),
         "in": 100, "out": 50, "cache_c": 0, "cache_r": 0},
        {"ts": (now - timedelta(days=1)).isoformat(timespec="seconds"),
         "in": 999, "out": 999, "cache_c": 0, "cache_r": 0},
    ])
    rc = main(["metrics", "--window", "5", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 1
    assert data[0]["in"] == 100

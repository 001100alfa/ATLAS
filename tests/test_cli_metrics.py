"""SPEC 023 — cache-hit metrics testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.orchestrator import planner as planner_mod


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return metrics


def _write_metrics_file(path: Path, records: list[dict]) -> None:
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_023_write_metric_dosya_yaratir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`_write_metric_for_data` dosya yoksa oluşturur."""
    metrics = _env(monkeypatch, tmp_path)
    data = {
        "usage": {
            "input_tokens": 100, "output_tokens": 50,
            "cache_creation_input_tokens": 20,
            "cache_read_input_tokens": 30,
        }
    }
    planner_mod._write_metric_for_data(data)
    assert metrics.is_file()
    obj = json.loads(metrics.read_text(encoding="utf-8").strip())
    assert obj["in"] == 100
    assert obj["out"] == 50
    assert obj["cache_c"] == 20
    assert obj["cache_r"] == 30
    assert "ts" in obj


def test_023_write_metric_append_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """İki kayıt append edilir — iki JSON satırı."""
    metrics = _env(monkeypatch, tmp_path)
    data1 = {"usage": {"input_tokens": 10, "output_tokens": 5}}
    data2 = {"usage": {"input_tokens": 20, "output_tokens": 10}}
    planner_mod._write_metric_for_data(data1)
    planner_mod._write_metric_for_data(data2)
    lines = metrics.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["in"] == 10
    assert json.loads(lines[1])["in"] == 20


def test_023_cmd_metrics_insan_format(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas metrics` insan formatı — toplam ve oran görünür."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "?"},
        {"ts": "t2", "in": 200, "out": 100,
         "cache_c": 0, "cache_r": 500, "cost": "?"},
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 2 çağrı" in out
    assert "input tokens:   300" in out
    assert "output tokens:  150" in out
    assert "cache read:     500" in out
    # cache-hit: 500 / (300 + 0 + 500) = 62.5%
    assert "62.5%" in out


def test_023_cmd_metrics_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas metrics --json` JSON liste döner."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "?"},
    ])
    rc = main(["metrics", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["in"] == 100


def test_023_cmd_metrics_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`atlas metrics --limit 2` son 2 kaydı özetler."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 0, "cache_c": 0, "cache_r": 0, "cost": "?"},
        {"ts": "t2", "in": 200, "out": 0, "cache_c": 0, "cache_r": 0, "cost": "?"},
        {"ts": "t3", "in": 300, "out": 0, "cache_c": 0, "cache_r": 0, "cost": "?"},
    ])
    rc = main(["metrics", "--limit", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    # son 2: 200 + 300 = 500
    assert "input tokens:   500" in out


def test_023_metrics_dosya_yok_no_op(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Metrics dosyası yoksa boş özet + exit 0."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "toplam: 0 çağrı" in out


def test_023_write_metric_disk_hata_sessiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Disk yazma hatası ana akışı bloklamamalı (sessiz no-op)."""
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "readonly" / "m.jsonl"))
    # Klasör oluşturmak isteyecek ama izinden bağımsız hata sessiz kalmalı
    # (yazma yolunda hata çıksa dahi exception yok)
    planner_mod._write_metric_for_data(
        {"usage": {"input_tokens": 1, "output_tokens": 1}}
    )
    # test geçerse hata bloklanmadı


# ─────────────────────────────────────────────────────────────────────────────
# SPEC 029 — atlas metrics --alert
# ─────────────────────────────────────────────────────────────────────────────


def _mixed_metrics(metrics: Path) -> None:
    """Test yardımcısı: %62.5 cache-hit oran veren iki kayıt."""
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "?"},
        {"ts": "t2", "in": 200, "out": 100,
         "cache_c": 0, "cache_r": 500, "cost": "?"},
    ])


def test_029_alert_alti_gecer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--alert 20` iken oran %62.5 → exit 0, uyarı yok."""
    metrics = _env(monkeypatch, tmp_path)
    _mixed_metrics(metrics)
    rc = main(["metrics", "--alert", "20"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "UYARI" not in captured.err
    assert "62.5%" in captured.out  # mevcut çıktı korunmuş


def test_029_alert_ustu_duser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--alert 80` iken oran %62.5 → exit 8, stderr'de UYARI."""
    metrics = _env(monkeypatch, tmp_path)
    _mixed_metrics(metrics)
    rc = main(["metrics", "--alert", "80"])
    assert rc == 8
    err = capsys.readouterr().err
    assert "UYARI" in err
    assert "cache-hit" in err
    assert "62.5" in err
    assert "80" in err


def test_029_alert_kayitsiz_duser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kayıt yoksa hit=0 → herhangi bir pozitif eşik altındadır → exit 8."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--alert", "10"])
    assert rc == 8
    err = capsys.readouterr().err
    assert "UYARI" in err


def test_029_alert_sifir_kapatir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--alert 0` alarmı kapatır — kayıtsız bile exit 0."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--alert", "0"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "UYARI" not in err


def test_029_alert_json_ile_birlesir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--alert 80 --json` iken JSON çıktı korunur, uyarı stderr'de, exit 8."""
    metrics = _env(monkeypatch, tmp_path)
    _mixed_metrics(metrics)
    rc = main(["metrics", "--alert", "80", "--json"])
    assert rc == 8
    captured = capsys.readouterr()
    # stdout hâlâ JSON liste
    data = json.loads(captured.out.strip())
    assert isinstance(data, list)
    assert len(data) == 2
    # stderr'de UYARI
    assert "UYARI" in captured.err


def test_029_alert_sinir_disi_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Geçersiz eşik (< 0 veya > 100) → SPEC HATASI + exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--alert", "150"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err

    rc = main(["metrics", "--alert", "-5"])
    assert rc == 2


# ═════════════════════════════════════════════════════════════════════
# SPEC 023.2 — metrics inflight istatistiği
# ═════════════════════════════════════════════════════════════════════


def test_0232_inflight_avg_max_basar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """3 kayıt (inflight 1, 2, 3) → avg=2.00, max=3, 3 kayıtta."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "2026-07-30T10:00:00", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "0.001", "inflight": 1},
        {"ts": "2026-07-30T10:01:00", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "0.001", "inflight": 2},
        {"ts": "2026-07-30T10:02:00", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "0.001", "inflight": 3},
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "inflight avg/max: 2.00 / 3" in out
    assert "3 kayıtta" in out


def test_0232_inflight_alani_yok_gorunmez(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Eski kayıtlarda inflight yok → satır BASILMAZ (bit-uyumluluk)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "2026-07-30T10:00:00", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "0.001"},
        # inflight alanı YOK
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "inflight avg/max" not in out


def test_0232_karma_inflight_ile_ilesiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """2 kayıt inflight'lı (1, 2), 1 kayıt inflight'sız → sadece 2 sayılır."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "2026-07-30T10:00:00", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "0.001", "inflight": 1},
        {"ts": "2026-07-30T10:01:00", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "0.001"},
        {"ts": "2026-07-30T10:02:00", "in": 100, "out": 50,
         "cache_c": 0, "cache_r": 0, "cost": "0.001", "inflight": 2},
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    # avg=1.5, max=2, 2 kayıtta
    assert "inflight avg/max: 1.50 / 2" in out
    assert "2 kayıtta" in out


def test_0232_json_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json` ham kayıtları döndürür (bit-uyumluluk); inflight alanı
    kayıtta olduğu gibi görünür."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "2026-07-30T10:00:00", "in": 10, "out": 5,
         "cache_c": 0, "cache_r": 0, "cost": "0.001", "inflight": 4},
    ])
    rc = main(["metrics", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert isinstance(data, list)
    assert data[0]["inflight"] == 4


# ═════════════════════════════════════════════════════════════════════
# SPEC 043 — atlas metrics --format prometheus
# ═════════════════════════════════════════════════════════════════════


def test_043_metrics_prometheus_temel_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--format prometheus` → v0.0.4 text; her metrik HELP+TYPE+değer."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 100, "out": 50, "cache_c": 20, "cache_r": 30},
        {"ts": "t2", "in": 200, "out": 100, "cache_c": 0, "cache_r": 500},
    ])
    rc = main(["metrics", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out

    # Zorunlu satırlar
    assert "# HELP atlas_metrics_records_total" in out
    assert "# TYPE atlas_metrics_records_total counter" in out
    assert "atlas_metrics_records_total 2" in out
    assert "atlas_metrics_tokens_prompt_total 300" in out
    assert "atlas_metrics_tokens_completion_total 150" in out
    assert "atlas_metrics_cache_creation_tokens_total 20" in out
    assert "atlas_metrics_cache_read_tokens_total 530" in out
    assert "atlas_metrics_cache_hit_ratio" in out
    assert "atlas_metrics_cost_usd_total" in out


def test_043_metrics_prometheus_inflight_yoksa_satirlar_basilmaz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`inflight` alanı olmayan kayıtlar → inflight_* satırları YOK."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 10, "out": 5, "cache_c": 0, "cache_r": 0},
    ])
    rc = main(["metrics", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_inflight_max" not in out
    assert "atlas_metrics_inflight_avg" not in out


def test_043_metrics_prometheus_inflight_varsa_avg_max(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`inflight` alanları varsa avg/max satırları basılır."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 10, "out": 5, "cache_c": 0, "cache_r": 0,
         "inflight": 1},
        {"ts": "t2", "in": 20, "out": 10, "cache_c": 0, "cache_r": 0,
         "inflight": 3},
        {"ts": "t3", "in": 30, "out": 15, "cache_c": 0, "cache_r": 0,
         "inflight": 2},
    ])
    rc = main(["metrics", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_metrics_inflight_max 3" in out
    assert "atlas_metrics_inflight_avg 2.0000" in out


def test_043_metrics_json_ve_format_prometheus_argparse_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """argparse mutually_exclusive_group → SystemExit (exit 2)."""
    _env(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["metrics", "--json", "--format", "prometheus"])
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    err_low = err.lower()
    assert (
        "not allowed with argument" in err
        or "argümanı" in err_low
        or "mutually" in err_low
    )


def test_043_metrics_default_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default (bayraksız) çıktı: SPEC 023 insan formatı — 'toplam:' satırı korunur."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 1, "out": 1, "cache_c": 0, "cache_r": 0},
    ])
    rc = main(["metrics"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS metrics" in out
    assert "toplam: 1 çağrı" in out
    assert "atlas_metrics_" not in out  # prometheus çıktısı sızmasın


def test_043_metrics_format_human_default_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format human = default davranış."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics_file(metrics, [
        {"ts": "t1", "in": 1, "out": 1, "cache_c": 0, "cache_r": 0},
    ])
    rc = main(["metrics", "--format", "human"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "=== ATLAS metrics" in out
    assert "atlas_metrics_" not in out

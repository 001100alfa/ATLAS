# Görev 090 — Teslim

`atlas metrics --group-by KEY --format prometheus [--with-cost]`.

## Uygulama

- `_cmd_metrics` group_by dalında:
  - **SPEC 081 MUTEX (`--group-by + --format prometheus`) KALDIRILDI**.
  - `--alert` MUTEX korunur (SPEC 081 karar geçerli — alert tekil değer).
  - Yeni Prometheus çıktısı: 5 base metric × N grup satırı.
  - `--with-cost` verildiyse 6. metric `atlas_metrics_group_cost_usd`.
  - Labels: `unit`, `key` — Prometheus text v0.0.4 escape (`\` `"` `\n`).
  - HELP+TYPE her metric için.
  - Değişken adı `group_lines` (mypy no-redef Prometheus dalındaki
    `lines`'la çakışma).

## Kanıt

- +9 yeni test (`tests/test_cli_metrics_group_by_prometheus.py`):
  - 5 base metric HELP+TYPE.
  - Labels: `unit=hour` + `key=...`.
  - Toplam değerler doğru (300, 150, 2).
  - `--with-cost` → cost_usd metric 10.5.
  - `--with-cost` YOK → cost_usd metric YOK.
  - `--alert` MUTEX (SPEC 081 hala geçerli).
  - `--group-by` YOK + prometheus → SPEC 043 tekil metrikler AYNI.
  - Deterministik sıra (2026-08-05 < 06 < 07).
  - HELP+TYPE 5+5 sayısı doğru.
- +1 güncelleme (`test_cli_metrics_group_by.py` — eski MUTEX testi
  yeni davranışa uyarlandı: rc==0 + group metric var).
- 1312 → **1321 yeşil** (+9), 12 skip.
- cov ~%91.44, mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 043 tekil Prometheus metrikleri AYNI (--group-by yoksa).
- SPEC 081 `--group-by + --alert` MUTEX KORUNDU.
- SPEC 084 `--with-cost` grup dict alanları AYNI (JSON/pretty
  tarafında).

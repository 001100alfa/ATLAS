# Görev 090 — İhtiyaç

SPEC 081 `--group-by + --format prometheus` MUTEX (exit 2) idi çünkü
"Prometheus tekil metrik, grup histogram olmalıydı YAGNI". SPEC 084
cost eklendikten sonra grup histogramı gerçek ihtiyaç: Grafana
dashboard'da "günlük cost trend" tek scrape ile.

## Kabul

- `atlas metrics --group-by KEY --format prometheus` **artık çalışır**
  (MUTEX KALDIRILDI — SPEC 081 kararı geri alındı).
- Yeni Prometheus metrikleri (labels: `unit`, `key`):
  - `atlas_metrics_group_records{...} N`
  - `atlas_metrics_group_tokens_in{...} N`
  - `atlas_metrics_group_tokens_out{...} N`
  - `atlas_metrics_group_cache_creation{...} N`
  - `atlas_metrics_group_cache_read{...} N`
- `--with-cost` ile birlikte ek metric:
  - `atlas_metrics_group_cost_usd{...} 3.14`
- HELP/TYPE yorumları her metric için (Prometheus text v0.0.4).
- Label değerleri deterministik sıra (key alfabetik).
- `--group-by + --format prometheus` VERİLMEZSE mevcut SPEC 043
  Prometheus çıktı AYNI (BİT-UYUMLU).
- `--group-by + --alert` MUTEX korunur (alert tekil hit-ratio; SPEC 081).

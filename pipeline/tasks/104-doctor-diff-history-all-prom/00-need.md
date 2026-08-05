# Görev 104 — İhtiyaç

SPEC 091 `--diff-history-all` toplu diff tablosu (pretty/JSON). CI/
Grafana dashboard için "hangi snapshot'ta kaç warning added/removed"
metrik olarak scrape edilebilmeli. Şu an `--format prometheus` MUTEX
exit 2. SPEC 090 (metrics) kalıbı ile MUTEX kaldırılıp per-snapshot
Prometheus çıktısı verilir.

## Kabul

- `atlas doctor --diff-history-all --format prometheus`.
- SPEC 091 `--format prometheus` MUTEX **KALDIRILDI** (sözleşme
  değişikliği — SPEC 090 rollback kalıbı ile simetrik).
- Prometheus metrikleri (labels: `snapshot_date`):
  - `atlas_doctor_history_warnings_added{...} N` (counter)
  - `atlas_doctor_history_warnings_removed{...} N` (counter)
  - `atlas_doctor_history_quality_deltas{...} N` (counter)
  - `atlas_doctor_history_has_regression{...} 0|1` (gauge)
  - `atlas_doctor_history_has_improvement{...} 0|1` (gauge)
- HELP/TYPE her metric için (Prometheus text v0.0.4).
- Label escape (`\` `"` newline).
- `--strict` ile ORTOGONAL (Prometheus çıktı, rc değişir).
- `--format prometheus` VERİLMEZSE SPEC 091 pretty/JSON AYNI.

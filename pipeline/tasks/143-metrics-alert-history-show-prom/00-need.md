# Görev 143 — İhtiyaç

SPEC 132 `--alert-history-show` pretty tablo + `--json`. Grafana/
Prometheus scrape için counter format gerek (kaç alert, kaç kanal).

## Kabul

- `atlas metrics --alert-history-show --format prometheus`.
- Metrikler (info-metric kalıbı):
  - `atlas_metrics_alert_history_total{}` = toplam kayıt (counter)
  - `atlas_metrics_alert_history_recent{}` = son N kayıt (counter)
  - `atlas_metrics_alert_channel_total{channel}` = kanal başına toplam
    (counter; email/webhook/slack + boş "-")
- HELP/TYPE her metric için.
- Label escape (`\` `"` newline).
- `--format prometheus` YOKSA SPEC 132 pretty/JSON AYNI (bit-uyumlu).
- `--format prometheus` + `--json` MUTEX (mevcut argparse grup zaten
  yakalar; test).
- `--limit N` counter'a etki eder (recent = tail).

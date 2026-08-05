# Görev 074 — İhtiyaç

SPEC 023 metrics.jsonl PR'da lokal — reviewer görüntülemek için depoyu
klonlamalı. SPEC 056/070 gate kalıbıyla `atlas-metrics.yml`: PR'da
human/JSON/prometheus özet artifact + insan-okunur PR comment.

## Kabul

- `.github/workflows/atlas-metrics.yml`:
  - push[main]+PR, `.atlas/metrics.jsonl` path filtresi.
  - Job `metrics`: ubuntu-latest, timeout 3dk.
  - metrics.jsonl varsa → 3 format üretilir (human/json/prometheus).
    Yoksa → boş placeholder.
  - artifact upload `always()` (fail'de bile).
  - PR comment sadece `has_data=true` + PR event.
- Fail step YOK — bilgi/artifact workflow'u (gate DEĞİL).

## Risk

- metrics.jsonl `.gitignore`'da (`.atlas/*`). Repo'da tracked değil,
  path filtresi ancak commit edilirse çalışır — genelde kullanıcı
  scheduled backup ile snapshot commit eder.

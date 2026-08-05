# Görev 074 — Teslim

`.github/workflows/atlas-metrics.yml` — SPEC 056/070 kardeşi metrics gate.

## Uygulama

- push[main]+PR, `.atlas/metrics.jsonl` path filtresi.
- Job `metrics` ubuntu-latest, timeout 3dk.
- 3 format artifact: human (txt), JSON, Prometheus.
- artifact upload `always()`; PR comment `has_data=true` + PR.

## Kanıt

- +6 workflow testi:
  - YAML valid + name.
  - Tetikleyiciler + path filtresi.
  - Permissions + concurrency.
  - 3 format (human/json/prometheus) üretilir.
  - PR comment PR + has_data koşullu.
  - Artifact upload `always()`.
- 1117 → **1123 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 023/043/056/070 BİT-UYUMLU.
- Kod tarafında değişiklik YOK.

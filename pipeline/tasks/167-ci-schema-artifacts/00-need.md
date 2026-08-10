# Görev 167 — İhtiyaç

SPEC 147 (`atlas-doctor.yml`), SPEC 152 (`atlas-ci-status.yml`),
SPEC 160 (`atlas-metrics.yml`), SPEC 161 (`atlas-vault.yml`) her biri
kendi schema artifact adımını üretti. Ancak her PR/push'ta CI ana
workflow (`ci.yml`) hızlı bir "hepsi bir arada" schema özeti gerek —
Grafana/scrape hedefleri için tek yerde 6 schema.

## Kabul

- `.github/workflows/ci.yml` yeni job: `schema-artifacts` (ubuntu-latest).
- Setup: checkout + Python 3.12 + `pip install -e ".[dev]"`.
- 6 schema komutu çalıştırır (hepsi native `--out --gzip` desteği ile):
  1. `doctor --schema --format prometheus --out doctor-schema.prom --gzip` (SPEC 134)
  2. `archive --schema --format prometheus --out archive-schema.prom --gzip` (SPEC 155)
  3. `metrics --schema --format prometheus --out metrics-schema.prom --gzip` (SPEC 162)
  4. `vault verify --schema --format prometheus --out vault-verify-schema.prom --gzip` (SPEC 145)
  5. `vault backup --schema --format prometheus --out vault-backup-schema.prom --gzip` (SPEC 163)
  6. `ai-cli status --schema --format prometheus --out ai-cli-status-schema.prom --gzip` (SPEC 156)
- Tek upload artifact: `atlas-schema-artifacts` (path: 6 .gz dosyası,
  retention-days=30, `if: always()`, `if-no-files-found: ignore`).
- Mevcut `quality` + `test-windows` job'ları DOKUNULMADI.
- Fail-safe: her komut `|| true` ile — biri düşse workflow devam.

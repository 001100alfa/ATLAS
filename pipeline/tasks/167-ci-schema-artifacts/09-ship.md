# Görev 167 — Teslim

`.github/workflows/ci.yml` yeni job `schema-artifacts` — 6 schema
komutu tek yerde toplu artifact.

## Uygulama
- Yeni job `schema-artifacts` (ubuntu-latest); mevcut `quality` +
  `test-windows` DOKUNULMADI.
- Setup: checkout + setup-python 3.12 + `pip install -e ".[dev]"`.
- 6 schema komutu (hepsi native `--out --gzip` desteği):
  1. `atlas doctor --schema --format prometheus --out doctor-schema.prom --gzip` (SPEC 134)
  2. `atlas archive --schema --format prometheus --out archive-schema.prom --gzip` (SPEC 155)
  3. `atlas metrics --schema --format prometheus --out metrics-schema.prom --gzip` (SPEC 162)
  4. `atlas vault verify --schema --format prometheus --out vault-verify-schema.prom --gzip` (SPEC 145)
  5. `atlas vault backup --schema --format prometheus --out vault-backup-schema.prom --gzip` (SPEC 163)
  6. `atlas ai-cli status --schema --format prometheus --out ai-cli-status-schema.prom --gzip` (SPEC 156)
- Her komutta `||` fallback (fail-safe SPEC 095/147/152 kalıbı) —
  biri düşse workflow devam eder.
- Tek upload artifact: `atlas-schema-artifacts` (6 .gz dosyası,
  retention-days=30, `if: always()`, `if-no-files-found: ignore`).
- Shell gzip YOK — SPEC 162/163 sayesinde hepsi native `--out --gzip`.

## Kanıt
- +7 test (`tests/test_github_workflows.py` SPEC 167 bölümü):
  1. `schema-artifacts` job var (ubuntu-latest)
  2. Setup: checkout + setup-python + pip install
  3. 6 schema step var (SPEC 134/155/162/145/163/156 hepsi)
  4. Her step native --out --gzip (shell gzip YOK) + `||` fallback +
     --schema + --format prometheus
  5. Upload step `atlas-schema-artifacts` + 6 .gz path
  6. Upload `if: always()`
  7. Mevcut `quality` + `test-windows` job'ları DOKUNULMADI (lint/mypy/pytest AYNI)
- Toplam workflow test 107 → **114 yeşil** (+7).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- ci.yml mevcut 2 job (`quality` + `test-windows`) DOKUNULMADI.
- SPEC 147/152/160/161 diğer workflow schema artifact adımları hâlâ
  aktif (paralel — ci.yml sadece "hepsi bir arada" özet üretir).
- 6 schema CLI komutunun contract'ı AYNI (SPEC 134/145/155/156/162/163).

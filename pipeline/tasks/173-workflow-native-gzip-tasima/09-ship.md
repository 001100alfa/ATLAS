# Görev 173 — Teslim

Workflow shell gzip → native `--out --gzip` taşıma (SPEC 162/163 sayesinde).

## Uygulama
- **`atlas-metrics.yml`** SPEC 160 step:
  - **eski**: `metrics --schema --format prometheus > metrics-schema.prom &&
    gzip -f metrics-schema.prom`
  - **yeni**: `metrics --schema --format prometheus --out
    metrics-schema.prom --gzip` (SPEC 162 native).
- **`atlas-vault.yml`** SPEC 161 vault backup step:
  - **eski**: `vault backup --schema --format prometheus > file &&
    gzip -f file`
  - **yeni**: `vault backup --schema --format prometheus --out
    vault-backup-schema.prom --gzip` (SPEC 163 native).
- `atlas-vault.yml` vault verify schema step AYNI (zaten native --out
  --gzip SPEC 145).
- `||` fallback her ikisi için KORUNUR (fail-safe SPEC 095/147 kalıbı).
- Upload artifact path DEĞİŞMEDİ (`metrics-schema.prom.gz`,
  `vault-backup-schema.prom.gz`).
- Step adı SPEC referansına SPEC 173 eklendi (kalıp).

## Kanıt
- +5 test (`tests/test_github_workflows.py` SPEC 173 bölümü):
  1. atlas-metrics metrics schema native --out --gzip (shell gzip YOK)
  2. atlas-vault vault backup schema native --out --gzip (shell gzip YOK)
  3. atlas-vault vault verify schema zaten native --out --gzip (SPEC 145)
  4. atlas-metrics fallback `||` KORUNUR
  5. atlas-vault backup schema fallback `||` KORUNUR
  6. atlas-ci-status SPEC 152 archive schema HÂLÂ shell gzip (sonraki tur adayı)
- Toplam workflow test 114 → **120 yeşil** (+6).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 145 vault verify --schema prom --out --gzip AYNI (zaten native).
- SPEC 152 atlas-ci-status archive schema shell gzip AYNI (sonraki tur adayı).
- SPEC 147 atlas-doctor schema native --out --gzip AYNI.
- Upload artifact path'leri AYNI (Grafana kaynakları etkilenmez).
- Fail-safe `||` fallback davranışı AYNI.

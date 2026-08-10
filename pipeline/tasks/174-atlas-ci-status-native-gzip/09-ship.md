# Görev 174 — Teslim

`atlas-ci-status.yml` shell gzip → native `--out --gzip` taşıma
(SPEC 155 sayesinde; SPEC 173 metrics/vault backup kardeşi).

## Uygulama
- SPEC 152 step:
  - **eski**: `archive --schema --format prometheus > archive-schema.prom &&
    gzip -f archive-schema.prom`
  - **yeni**: `archive --schema --format prometheus --out
    archive-schema.prom --gzip`
- Step adı SPEC referansına `152/155/174` eklendi.
- `||` fallback KORUNUR.
- Upload artifact adı + path DEĞİŞMEDİ (`atlas-ci-status-schema`,
  `archive-schema.prom.gz`).

## Kanıt
- +3 test SPEC 174 (`tests/test_github_workflows.py`):
  1. Native `--out --gzip` mevcut; shell `gzip -f` YOK
  2. Fallback `||` KORUNUR
  3. Upload artifact adı + path AYNI (SPEC 152)
- Eski SPEC 173 "hâlâ shell" testi silindi — artık native.
- SPEC 152 mevcut 5 test AYNI çalışıyor (gzip kelime eşleşmesi
  `--gzip`'te de var, kalıp bit-uyumlu).
- Toplam workflow test 120 → **122 yeşil** (net +2: +3 SPEC 174 −1 SPEC 173).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 155 archive --schema prom --out --gzip AYNI.
- SPEC 152 upload adı + path + `if: always()` AYNI.
- SPEC 141 Post ci-status alert webhook step AYNI.
- SPEC 089/125 drift-scan davranışı AYNI.
- 4 workflow (atlas-doctor + atlas-metrics + atlas-vault +
  atlas-ci-status) artık HEPSİ native `--out --gzip` — shell gzip
  sadece ci.yml SPEC 167 özet job'da opsiyonel fallback.

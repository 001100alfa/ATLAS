# Görev 152 — Teslim

`.github/workflows/atlas-ci-status.yml` archive schema prometheus
gzip artifact adımı (SPEC 147 kalıbı, SPEC 151 üstüne).

## Uygulama
- Yeni step: `Generate archive schema prometheus artifact (SPEC 152)`.
- `atlas archive --schema --format prometheus > archive-schema.prom &&
  gzip -f archive-schema.prom` (shell tabanlı; SPEC 155 --out --gzip
  gelene kadar).
- `||` fallback (fail-safe SPEC 095/147 kalıbı).
- Yeni upload step: `Upload atlas-ci-status schema artifact (SPEC 152)`
  (name=`atlas-ci-status-schema`, path=`archive-schema.prom.gz`,
  retention-days=30, `if: always()`, `if-no-files-found: ignore`).
- Mevcut Python setup DOKUNULMADI (gen_ci_badges.py için gerekli).
- Yeni `Setup uv` + `Install ATLAS` adımları eklendi.
- Conditional YOK schema step için — kısa devre her zaman çalışır.

## Kanıt
- +5 test (`tests/test_github_workflows.py` SPEC 152 bölümü):
  - schema step var + doğru komut/argümanlar
  - `||` fallback
  - upload step + name/path
  - `if: always()`
  - Setup uv + Install ATLAS + mevcut Setup Python korundu
- Toplam workflow test 90 → **95 yeşil** (+5).
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 089 drift-scan davranışı AYNI.
- SPEC 125 drift diff artifact upload AYNI.
- SPEC 141 alert-webhook gate AYNI.
- Mevcut Python setup + gen_ci_badges.py adımları DOKUNULMADI.

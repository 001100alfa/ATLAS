# Görev 099 — İhtiyaç

SPEC 088 `--outdated --json` tek büyük JSON basar. CI pipeline'da
paket başına iş (issue aç, PR aç, slack post) için stream tüketici
uygun; NDJSON `while read; jq -r .name` doğal akış.

## Kabul

- `atlas ai-cli list --outdated --json-lines`.
- Her paket tek satır: `{"name":..,"expected":..,"installed":..}`
  (JSON --outdated şemasıyla AYNI alanlar, `path` YOK — top-level'da
  değil, satır-başına).
- Son satır özet: `{"type":"summary","path":..,"outdated":N,"total_deps":N}`.
- `--outdated` gerekli — `--json-lines` yalnız `--outdated` ile
  anlamlı. Aksi hâlde SPEC HATASI exit 2.
- `--json` ile MUTEX (iki farklı JSON format).
- `--strict` ile ORTOGONAL (bulgu var + strict → exit 4, NDJSON hâlâ
  basılır).
- `--json-lines` VERİLMEZSE SPEC 088 BİT-UYUMLU.

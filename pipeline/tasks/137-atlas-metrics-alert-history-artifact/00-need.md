# Görev 137 — İhtiyaç

SPEC 126 `.atlas/alert-history.jsonl` NDJSON log yerelde tutulur. CI'de
alert tetiklenirse workflow bunu artifact olarak upload etmeli — retro
analiz için erişim.

## Kabul

- `.github/workflows/atlas-metrics.yml` upload artifact path listesine
  `.atlas/alert-history.jsonl` eklenir (varsa).
- `hashFiles(...) != ''` conditional YERİNE `path`'e dosya adı
  eklemek yeterli (actions/upload-artifact `if-no-files-found: ignore`
  ile hata vermez).
- `if-no-files-found: ignore` yeni step ayarı — yoksa uyarı yok.
- Mevcut 5 artifact (human/json/prom/cost/group-day.prom.gz)
  DOKUNULMADI (BİT-UYUMLU).

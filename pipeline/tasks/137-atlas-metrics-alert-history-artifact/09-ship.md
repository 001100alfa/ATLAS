# Görev 137 — Teslim

`atlas-metrics.yml` alert-history artifact.

## Uygulama
- Upload artifact path listesine `.atlas/alert-history.jsonl` eklendi.
- `if-no-files-found: ignore` — dosya yoksa uyarı yok (SPEC 126 alert
  tetiklenmediği turda log da yok).
- Mevcut 5 artifact DOKUNULMADI.

## Kanıt
- +2 test; 1545 → **1547 yeşil**.

# Görev 133 — İhtiyaç

SPEC 127 `archive --restore --json` tek satır JSON dict. CI pipeline'da
`while read; jq` stream-based tüketici için NDJSON gerek — apply
sonucunda tek satır (extract edilen dosya adları teker teker) olabilir
ama minimum sözleşme: header + summary satırları.

## Kabul

- `atlas archive --restore <id> --json-lines [--apply]`.
- Dry-run stream:
  - `{"type":"plan","task_id","archive","target","conflict":bool}`
  - `{"type":"summary","task_id","mode":"dry-run"}`
- Apply stream:
  - `{"type":"plan","task_id","archive","target","conflict":false}`
  - `{"type":"restored","task_id","target","archive"}`
  - `{"type":"summary","task_id","mode":"apply","restored":true}`
- `--json` + `--json-lines` MUTEX exit 2.
- Hata durumu (RestoreError) → NDJSON basmaz (stderr SPEC HATASI; rc 3/6).
- `--json-lines` VERİLMEZSE SPEC 033/127 BİT-UYUMLU.

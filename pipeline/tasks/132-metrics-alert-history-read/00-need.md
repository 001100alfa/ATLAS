# Görev 132 — İhtiyaç

SPEC 126 `.atlas/alert-history.jsonl` NDJSON log yazar; **okuma modu**
yok. Post-mortem için "son N alert" görmek gerek.

## Kabul

- `atlas metrics --alert-history-show [PATH] [--limit N] [--json]`.
- Default path: `.atlas/alert-history.jsonl` (SPEC 126 kalıbı).
- `--limit N` (default 10) son N alert.
- `--json` → NDJSON stream (her satır rec + son satır summary).
- Pretty: tablo `ts | hit_ratio | threshold | channels`.
- Dosya yok → boş çıktı + rc 0 (info komut).
- `--alert-history-show` bilgi komutu — normal metrics özet çalıştırmaz.
- Mevcut metrics komutları (SPEC 023/029/...) DOKUNULMADI.

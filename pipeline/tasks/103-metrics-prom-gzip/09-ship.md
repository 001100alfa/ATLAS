# Görev 103 — Teslim

`atlas metrics --group-by --format prometheus --out PATH --gzip`.

## Uygulama

- `_cmd_metrics` başında `--gzip` + not `--out` MUTEX exit 2.
- Group Prometheus `--out` dalında:
  - PATH `.gz` uzantı yok → auto-suffix `.gz` ekle.
  - `gzip.open(op, "wt", encoding="utf-8")` — Windows/POSIX uyumlu.
  - `--gzip` yok → düz `write_text` (SPEC 096 BİT-UYUMLU).
- Değişken adı `prom_text` (mypy `payload` scope narrow çakışması
  önlemi — SPEC 064 alert-webhook `payload` dict ile isim çakışması).
- Parser: `--gzip` action="store_true".

## Kanıt

- +7 test (`tests/test_cli_metrics_prom_gzip.py`):
  - `.gz` uzantı yok → auto-suffix.
  - `.gz` uzantılı → aynen (çift `.gz.gz` yok).
  - Decompress + düz metin İÇERİK AYNI (bit-uyumluluk).
  - `--gzip` --out yok → exit 2.
  - Gzip magic bytes (1f 8b) doğrulama.
  - `--gzip` YOKSA düz metin (magic YOK).
  - Auto-suffix + dizin çakışması → `<dir>.gz` yeni dosya (başarı 0).
- 1381 → **1388 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 096: düz `--out` (gzip yok) AYNI.
- SPEC 090: stdout Prometheus grup metrikleri AYNI.
- SPEC 064: `_post_alert_webhook` payload tipi DOKUNULMADI (isim
  çakışması `prom_text` ile giderildi).

# Görev 169 — Teslim

`atlas metrics --alert PCT --alert-window MINUTES`.

## Uygulama
- `_cmd_metrics` normal dispatcher'da alert değerlendirmesi için AYRI
  zaman-pencereli filtre.
- `records_raw = list(records)` `--window` uygulanmadan ÖNCE saklanır
  (orjinal liste).
- `--alert-window MINUTES` verildiğinde alert için `_filter_records_by_window(
  records_raw, alert_window_min)` sonucundan hit_ratio hesaplanır.
- `--alert-window` YOKSA `alert_*` değişkenleri mevcut tail değerlerine
  eşitlenir → SPEC 029 bit-uyumlu davranış.
- Geçersiz değer (`<= 0`) → SPEC HATASI exit 2.
- Alert bildirim kanalları (email/webhook/slack) `alert_hit_ratio` +
  `alert_records_count` + `alert_tokens_*` + `alert_cache_*` kullanır.
- Alert-history NDJSON payload'a **YENİ ALANLAR** (SPEC 032.4 bit-uyumlu):
  - `alert_window_minutes`: int (yalnız --alert-window verildiğinde)
  - `alert_window_records`: int
- Webhook payload'a **YENİ ALAN**:
  - `alert_window_minutes`: int (yalnız --alert-window verildiğinde)
- Email body'ye `window: N dakika` satırı (yalnız --alert-window verildiğinde).
- Slack text'e `· window: \`Nm\`` eki (yalnız --alert-window verildiğinde).
- Parser: `--alert-window MINUTES` yeni argüman (positive float).

## Kanıt
- +7 test (`tests/test_cli_metrics_alert_window.py`) — kontrollü ts
  ile deterministik:
  1. Eski yüksek + yeni düşük hit + window 60 → ALARM (exit 8)
  2. Eski düşük + yeni yüksek hit + window 60 → alarm YOK
  3. --alert-window YOK → mevcut davranış (tail üzerinden)
  4. --alert-window 0 → SPEC HATASI exit 2
  5. History payload'a yeni alanlar (alert_window_minutes + _records)
  6. --alert-window YOK → yeni alanlar YAZILMAZ (bit-uyumlu)
  7. --alert-window --alert olmadan → etkisiz (alarm zaten kapalı)
- metrics regresyon 222 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 023 normal metrics çıktısı AYNI (--alert-window yoksa).
- SPEC 029 --alert PCT + exit 8 davranışı AYNI (yoksa).
- SPEC 076 --window MINUTES özet filtresi AYNI (bağımsız).
- SPEC 043 --format prometheus AYNI.
- SPEC 059/064/068 alert kanalları payload alanlarına **ekleme**
  yapıldı (bit-uyumlu — --alert-window yoksa aynı).
- SPEC 126 alert-history NDJSON şeması bit-uyumlu (yeni alanlar yalnız
  --alert-window ile yazılır).

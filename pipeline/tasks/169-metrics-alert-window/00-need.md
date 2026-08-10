# Görev 169 — İhtiyaç

SPEC 029 `--alert PCT` cache-hit oranını `tail` (--limit N kayıt) üzerinden
değerlendiriyor. SPEC 076 `--window MINUTES` mevcut ama hem özet hem tail'i
filtreliyor (birlikte etki). Kullanıcı zaman-tabanlı alert isteyebilir:
"limit 1000 kayıt özet göster; ama sadece son 60 dakikadaki cache-hit
%30 altında ise alert."

## Kabul

- `atlas metrics --alert PCT --alert-window MINUTES`.
- `--alert-window MINUTES` verildiğinde alert değerlendirmesi için AYRI
  window: `records_raw` (--window uygulanmadan önceki orjinal liste)
  üzerinden `_filter_records_by_window(records_raw, alert_window)` sonucu
  kullanılır — TAIL bağımsız.
- `--alert-window` YOKSA mevcut davranış AYNI (tail üzerinden alert).
- Geçersiz değer (`<= 0`) → SPEC HATASI exit 2.
- `--alert-window` `--alert` olmadan verilirse etkisiz (uyarı yok — mevcut
  bit-uyumluluk kalıbı; alarm zaten kapalı).
- Alert-history NDJSON kaydına yeni alanlar (SPEC 126 üstüne):
  - `alert_window_minutes`: int (--alert-window değeri; yoksa alan yok)
  - `alert_window_records`: int (window'daki kayıt sayısı; yoksa alan yok)
- Parser: `--alert-window MINUTES` yeni argüman (positive int).
- Payload'a mevcut alanlar AYNI (bit-uyumluluk: alan-ekleme SPEC 032.4).
- SPEC 029/043/076/126 mevcut davranışlar BİT-UYUMLU.

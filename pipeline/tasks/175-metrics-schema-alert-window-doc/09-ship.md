# Görev 175 — Teslim

`atlas metrics --schema` JSON'a `alert_options` + `alert_payload`
alanları (SPEC 032.4 bit-uyumlu; SPEC 164 sub_commands kalıbı).

## Uygulama
- SPEC 153 `metrics_schema` JSON'a **iki yeni alan**:
  - `alert_options`: 7 CLI seçeneği (SPEC 029/059/064/068/126/132/169)
    her biri `{name, spec, desc}`.
  - `alert_payload`: 13 alan (9 mevcut + 2 SPEC 126 history-only +
    1 SPEC 064 webhook-only + 2 SPEC 169 alert-window-only)
    her biri `{name, type, when, spec}`.
- Prometheus çıktısına **EKLENMEDİ** (SPEC 164 YAGNI kalıbı — mevcut
  4 metric aile sayısı korunur).
- notes: SPEC 169 + SPEC 175 satırları eklendi.
- Mevcut top_level/exit_codes/formats DOKUNULMADI.

## Kanıt
- +8 test (`tests/test_cli_metrics_schema_alert_window_doc.py`):
  1. alert_options 7 seçenek adı mevcut
  2. Her seçenek doğru SPEC numarası (029/059/064/068/126/132/169)
  3. alert_payload 9 mevcut alan + 2 SPEC 169 alanı
  4. `--alert-window` alanları `when` alanında SPEC 169'a bağlı
  5. `channels` history-only + `message` webhook-only
  6. notes'a SPEC 169 + SPEC 175 satırları
  7. Prometheus çıktısı DOKUNULMADI (4 metric aile AYNI)
  8. SPEC 153 mevcut top_level/exit_codes/formats bit-uyumlu
- metrics_schema regresyon 35 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 153 JSON şeması geriye uyumlu (SPEC 032.4 alan-ekleme).
- SPEC 157/162 Prometheus çıktısı AYNI (4 metric aile, alert_options yok).
- SPEC 169 --alert-window davranışı AYNI (SPEC 175 sadece belgeler).
- SPEC 023/029/043/126/132 mevcut metrics davranışları AYNI.

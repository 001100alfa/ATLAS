# Görev 179 — Teslim

`atlas metrics --alert-history-show --schema [--pretty]` (SPEC 040/136/
146/149/153/154 kalıbı; SPEC 132 alert-history record biçimi şeması).

## Uygulama
- `_cmd_metrics` --alert-history-show bloğu başında `--schema` kısa
  devre eklendi.
- **Kritik**: SPEC 153 `metrics --schema` kısa devresi güncellendi —
  `alert_history_show is not None` ise ORAYA girmez (SPEC 179 dalına bırakır):
  ```python
  if args.schema and args.alert_history_show is None:  # SPEC 153
  if show_path is not None:
      if args.schema: ...  # SPEC 179
  ```
- Şema alanları:
  - `schema_version` = "1"
  - `record_fields`: 12 alan (SPEC 126 10 always + SPEC 169 2 opsiyonel).
    Her biri `{name, type, when, spec, desc}`.
  - `summary_fields`: 4 alan (`type`, `path`, `count`, `total`).
  - `exit_codes`: 0/2/4 (SPEC 132/148).
  - `formats`: human/json/prometheus (SPEC 132/143).
  - `notes`: SPEC 126/132/139/143/144/148/179 referansları.
- Parser DEĞİŞMEDİ (--schema + --pretty zaten SPEC 153'den var).
- Log dosyası gerekmez (kısa devre).

## Kanıt
- +11 test (`tests/test_cli_metrics_alert_history_show_schema.py`):
  1. --schema log gerekmez (kısa devre)
  2. record_fields 10 zorunlu + 2 opsiyonel (SPEC 126/169)
  3. SPEC 169 alanları `when` alanında koşula bağlı
  4. summary_fields 4 alan
  5. exit_codes 0/2/4
  6. formats human/json/prometheus + doğru SPEC
  7. notes SPEC referansları (126/132/139/143/144/148/179)
  8. --pretty indent=2
  9. --alert-history-show argümansız (default path) + --schema
  10. --schema YOKSA SPEC 132 normal show AYNI (bit-uyumlu)
  11. SPEC 153 `metrics --schema` (alert-history-show olmadan) AYNI
- metrics regresyon 243 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 132 `--alert-history-show` normal davranışı AYNI (--schema yoksa).
- SPEC 139/143/144/148 --json/--out/--format prometheus/--strict AYNI.
- SPEC 153 `metrics --schema` (alert-history-show YOK) AYNI çalışır +
  SPEC 175 alert_options/alert_payload alanları KORUR.
- SPEC 175 alert_payload alanları bit-uyumlu; SPEC 179 farklı bir
  perspektif (record_fields = log satırı; alert_payload = 175'te
  aynı yapının seçenek katalogu).

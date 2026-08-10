# Görev 184 — Teslim

`atlas metrics --alert-history-show --format json-lines [--out PATH]`
(SPEC 087/166/171/172 kalıp tutarlılığı; `--json` bit-uyumlu alias).

## Uygulama
- SPEC 132 `--alert-history-show` bloğuna `--format json-lines` desteği:
  - Yeni yerel `ah_jsonl = args.format == "json-lines"`.
  - MUTEX: `--json` + `--format json-lines` → SPEC HATASI exit 2
    (aynı çıktı; iki bayrak anlamsız). Argparse mutex grubu zaten
    reddediyor — açık test var.
  - `show_json_mode = --json OR ah_jsonl` → aynı NDJSON kod yolu.
- SPEC 139 `--out` sözleşmesi genişletildi: "yalnız --json,
  --format json-lines veya --format prometheus ile".
- SPEC 179 schema JSON `formats` alanına `json-lines` (spec=184) eklendi.
- SPEC 179 schema notes'a SPEC 184 satırı eklendi.
- Normal metrics modda `--format json-lines` REDDEDER
  (SPEC 158/166/171 kalıbı) → SPEC HATASI exit 2.
- Parser: `--format` choices'a `json-lines` eklendi (mevcut prometheus'a).

## Kanıt
- +8 test (`tests/test_cli_metrics_alert_history_show_jsonl.py`):
  1. --format json-lines NDJSON stream + summary
  2. --format json-lines çıktısı --json çıktısı ile birebir (bit-uyumlu)
  3. --json + --format json-lines argparse mutex exit 2
  4. --format json-lines --out PATH dosyaya, stdout boş
  5. Normal metrics + --format json-lines → SPEC HATASI exit 2 (yeni MUTEX)
  6. --out yalnız json/json-lines/prometheus ile (human'da reddet)
  7. --format json-lines + --strict → NDJSON + exit 4 (SPEC 148)
  8. SPEC 179 schema `formats` alanında `json-lines` (spec=184)
- metrics regresyon 251 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 132 human default (--format/--json yoksa) AYNI.
- SPEC 132 `--json` NDJSON çıktısı AYNI (--format json-lines bit-uyumlu).
- SPEC 143/144 --format prometheus + --out --gzip AYNI.
- SPEC 148 --strict + exit 4 AYNI.
- SPEC 179 --alert-history-show --schema JSON alanları AYNI + formats
  listesine yeni öğe (SPEC 032.4 alan-ekleme bit-uyumlu).

## Yeni MUTEX
- Normal metrics (--alert-history-show YOK) + `--format json-lines`
  → SPEC HATASI exit 2. (SPEC 158/166/171 doctor/archive kalıbı ile
  tutarlı; metrics çıktı biçimleri özet için human/prometheus'la
  sınırlı, NDJSON alert-history-show'un özelliği.)

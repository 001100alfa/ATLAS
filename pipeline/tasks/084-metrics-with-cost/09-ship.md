# Görev 084 — Teslim

`atlas metrics --group-by KEY --with-cost [--json]`.

## Uygulama

- `_group_cost_usd(group, price_in, price_out)`: SPEC 043 Prometheus
  formülü AYNI:
  `in*Pin + cc*Pin*1.25 + cr*Pin*0.1 + out*Pout` / 1M.
- `_cmd_metrics`: `--with-cost` + `--group-by` yoksa SPEC HATASI exit 2.
- `--group-by` dalında: env fiyat oku (`_read_llm_prices`), grup dict'e
  `cost_usd` alanı ekle (round 6).
- Pretty: env 0 ise UYARI stderr; yeni sütun `cost` ($ prefix, 6 basamak).
- JSON: mevcut alanlara ek `cost_usd`.
- Parser: `--with-cost` action="store_true".

## Kanıt

- +9 test (`tests/test_cli_metrics_with_cost.py`):
  - `_group_cost_usd` birim (zero prices, hesap, boş alan).
  - `--group-by hour --with-cost --json` grup dict'te cost_usd (10.5$).
  - Env yok → cost 0, UYARI stderr.
  - Pretty tabloda cost sütunu + $ prefix.
  - `--with-cost` tek başına (group-by yok) → SPEC HATASI exit 2.
  - `--with-cost` YOK → SPEC 081 bit-uyumlu (cost_usd YOK).
  - Cache hesabı (cache_c 1.25 katsayı).
  - İki günlük ayrı gruplar ayrı cost.
- 1254 → **1264 yeşil** (+10 test, +1 helper birim; toplam sayı test
  dosyasında 9 fonksiyon), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 081: `--with-cost` VERİLMEZSE grup dict alanları AYNI.
- SPEC 043 Prometheus cost formülü DEĞİŞMEDİ (extract helper aynı).
- Diğer metrics komutları (default, --json, --format prometheus,
  --alert, --serve, --window) etkilenmedi.

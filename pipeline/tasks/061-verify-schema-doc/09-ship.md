# Görev 061 — Teslim

`docs/api/vault-verify-schema.json` — SPEC 042 VerifyReport JSON Schema.

## Uygulama

- **Yeni dosya**: `docs/api/vault-verify-schema.json`.
- Draft-07 (`$schema` alanı).
- Root: `object`, `additionalProperties: false`, 7 zorunlu alan.
- `broken_links[]`: `{from, to}` (literal `"from"` JSON, Python'daki `frm`
  alanı `to_dict`'te `"from"` olarak yazılır).
- Sayaçlarda `minimum: 0`.

## Kanıtlar

- +12 test (`tests/test_verify_schema_doc.py`):
  - Şema dosya bütünlüğü (mevcut, valid JSON, Draft-07 imzası)
  - Root object + additionalProperties=false + zorunlu alan seti
  - `broken_links` item şeması
  - integer alanların minimum=0
  - Canlı `to_dict()` → temiz vault (2 test)
  - Manuel `VerifyReport` → şema uyumlu
  - **Negatif**: ekstra alan reddi + eksik zorunlu reddi + yanlış tip reddi
- 995 → **1007 yeşil**, 12 skip, cov aynı %91.50 (kod eklenmedi).
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- `atlas vault verify --json` çıktı YAPISI değişmedi — şema ONA UYAR.
- İlgili SPEC 042/052/046/058 hepsi BİT-UYUMLU.

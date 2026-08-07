# Görev 142 — Teslim

`doctor --schema` metric ailesi genişletme.

## Uygulama
- `_doctor_schema_descriptor()` 3 yeni alan:
  - `backend_options` (ATLAS_LLM stub/anthropic/acp)
  - `retry_pricing_envs` (SPEC 013/026/044 env listesi)
  - `storage_envs` (ATLAS_VAULT/AUDIT/SANDBOX/...)
- Prometheus dalı 2 yeni metric ailesi:
  - `atlas_doctor_schema_backend_option{name,value}` = 1
  - `atlas_doctor_schema_env{group,name}` = 1
- Toplam metric ailesi: 4 → 6 (bit-uyumlu ekleme).
- SPEC 128 test güncellendi (4 → 6 kabul).

## Kanıt
- +6 yeni test (`test_cli_doctor_schema_ext.py`).
- +1 test güncelleme (SPEC 128 sayı 4→6).
- 1588 → **1594 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 040 JSON şeması **BİT-UYUMLU EKLEME** — mevcut alanlar
  (top_level/quality_fields/exit_codes/notes) korundu.
- SPEC 128 4 base metric ailesi AYNI + 2 yeni.

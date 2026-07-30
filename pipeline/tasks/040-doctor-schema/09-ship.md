# Görev 040 — Teslim

`atlas doctor --schema [--pretty]` — sağlık kontrolü YAPMAZ; JSON
şema tanımını yayımlar.

## Çıktı şeması
```json
{
  "schema_version": "1",
  "top_level":     [{name, type, desc}, ...],
  "quality_fields":[{name, spec, desc}, ...],
  "exit_codes":    {"0": ..., "8": ..., "9": ...},
  "notes":         [...]
}
```

## Kanıtlar
- `top_level` içinde schema_version/backend/quality/storage/warnings
- `quality_fields` içinde decisions_drift/entry_count/vault_health/scan_src
- `--pretty` → 20+ satır JSON
- Boş dizinde çağrı → hata YOK (`_collect_doctor_report` atlanır)
- +5 test (747 yeşil, cov %90.68)

## Bakım notu
`_doctor_schema_descriptor` ve `_collect_doctor_report` eş güncel
tutulmalı: yeni alan eklendikçe iki yer birlikte değişir. Major
bump'da `schema_version` de değişir.

## Değişmeyen sözleşme
- `atlas doctor` (bayraksız), `--json`, `--strict`, `--scan-src`,
  `--ping`, `--pretty` bit-uyumlu.

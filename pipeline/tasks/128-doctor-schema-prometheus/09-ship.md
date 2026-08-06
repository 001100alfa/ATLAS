# Görev 128 — Teslim

`atlas doctor --schema --format prometheus` (info-metric ailesi).

## Uygulama
- **SPEC 047 MUTEX rollback** (3.): `--schema` mutex grubundan çıkarıldı;
  `--json` ve `--format` grup içinde kaldı. `--schema` kısa devre kendi
  başına info-metric text yayımlar.
- 4 metric ailesi:
  - `atlas_doctor_schema_version{version}` = 1
  - `atlas_doctor_schema_top_level_field{name, type}` = 1 (her top-level)
  - `atlas_doctor_schema_quality_field{name, spec}` = 1 (her quality)
  - `atlas_doctor_schema_exit_code{code}` = 1 (her exit code)
- HELP/TYPE her metric için (Prometheus text v0.0.4 info-metric kalıbı).
- Label escape: `\` `"` `\n`.
- `--format` YOKSA SPEC 040 JSON çıktı AYNI.

## Kanıt
- +6 yeni test (`tests/test_cli_doctor_schema_prom.py`).
- +2 test güncelleme (eski MUTEX → yeni davranış:
  `test_047_128_...no_longer_mutex`).
- 1520 → **1526 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 040 `--schema` JSON çıktı BİT-UYUMLU (--format yoksa).
- SPEC 047 --json + --format MUTEX KORUNDU (grup içinde).

## Sözleşme değişikliği (3. rollback)
- SPEC 047 MUTEX: `--schema` grup üyeliği kaldırıldı (`--json` ve
  `--format` ile artık birlikte kullanılabilir; --schema kısa devre
  önce çalışır, diğer bayraklar bilgi komutunda ignored).

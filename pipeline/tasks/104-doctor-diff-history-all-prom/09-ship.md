# Görev 104 — Teslim

`atlas doctor --diff-history-all --format prometheus`.

## Uygulama

- **SPEC 091 MUTEX (`--format prometheus`) KALDIRILDI** (SPEC 090
  rollback kalıbı ile simetrik — 2. sözleşme değişikliği).
- SPEC 091 blogunda snapshots üretildikten sonra `--format prometheus`
  dalı:
  - 5 metric: `warnings_added` (counter), `warnings_removed` (counter),
    `quality_deltas` (counter), `has_regression` (gauge 0/1),
    `has_improvement` (gauge 0/1).
  - Labels: `snapshot_date` (escape `\` `"` `\n`).
  - HELP/TYPE her metric için.
- `--strict` ile ORTOGONAL (Prometheus çıktısı basılır, rc SPEC 097
  ile 9 döner regresyon varsa).
- SPEC 040 `--schema` kısa devre BİT-UYUMLU.

## Kanıt

- +8 yeni test (`tests/test_cli_doctor_diff_history_all_prom.py`):
  - 5 metric HELP+TYPE ailesi.
  - `snapshot_date` label doğrulama.
  - counter/gauge tip kontrolü.
  - has_regression/improvement 0|1.
  - --strict + regresyon → rc in {0,9}, çıktı basılır.
  - `--format prometheus` YOKSA pretty AYNI.
  - `--format prometheus` YOKSA + --json AYNI.
  - 5+5 HELP+TYPE sayısı.
- +1 güncelleme (`test_cli_doctor_diff_history_all.py` — eski MUTEX
  testi yeni davranışa uyarlandı: rc==0 + prometheus çıktı).
- 1388 → **1396 yeşil** (+8), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 091 pretty tablo + JSON şeması AYNI (--format prometheus yoksa).
- SPEC 097 --strict exit 9 davranışı prometheus'ta da korunur.
- SPEC 057 delta şeması AYNI.

# Görev 062 — Teslim

`atlas doctor --auto-baseline` + `--save-baseline [PATH]`.

## Uygulama

- `_DEFAULT_DOCTOR_BASELINE = Path(".atlas/doctor-baseline.json")` sabiti.
- `_cmd_doctor`:
  - `--save-baseline` verildiyse: 4-yollu mutex (diff/auto/serve/prometheus),
    hedef path (default veya explicit), `mkdir -p parents`, JSON indent=2 yaz.
  - `--auto-baseline` verildiyse: `--diff` ile mutex; default path yoksa
    nazik uyarı + exit 0 (ilk çalıştırma); varsa `diff_baseline`'a atanır
    (SPEC 057 dallanmasına düşer).
- Parser: `--auto-baseline` (store_true) + `--save-baseline PATH`
  (nargs="?", const=default).

## Kanıt

- +11 test (`tests/test_cli_doctor_auto_baseline.py`):
  - Default path sabiti.
  - `--save-baseline` (default yol, custom path, 3 mutex).
  - `--auto-baseline` (ilk çalıştırma nazikliği, save→auto self-compare,
    diff mutex, strict regresyon exit 9).
  - Default doctor bit-uyumlu.
- 1007 → **1018 yeşil**, 12 skip, cov aynı %91.50+.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 057 `--diff BASELINE_JSON` BİT-UYUMLU (auto-baseline sadece
  kaynağı otomatik veriyor).
- Diğer doctor modları (bayraksız, --json, --schema, --format, --serve,
  --strict, --scan-src, --http-check, --ping, --pretty) BİT-UYUMLU.

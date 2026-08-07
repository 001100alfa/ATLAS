# Görev 148 — Teslim

`atlas metrics --alert-history-show --strict`.

## Uygulama
- SPEC 132 bloğunda `show_strict` bayrağı + `show_exit_rc`.
- `history_records` >=1 + `--strict` → `show_exit_rc = 4`.
- 3 dal (Prometheus/JSON/pretty) → çıktı basılır, `SAĞLIK BAŞARISIZ`
  stderr, `return show_exit_rc`.
- Log boş → `show_exit_rc = 0` (bit-uyumlu).
- Parser: `--strict` action="store_true" (metrics'e eklendi).
- SPEC 094 (ai-cli --outdated --strict) exit 4 kalıbıyla simetrik.

## Kanıt
- +6 test (`tests/test_cli_metrics_alert_history_show_strict.py`).
- 1616 → **1622 yeşil**, mypy/ruff/scan temiz.

## Değişmeyen sözleşme
- SPEC 132/143/144: --strict yoksa exit 0 AYNI.
- SPEC 029: metrics normal (--alert-history-show yok) `--strict` mevcut
  değil — bu bayrak alert-history-show özel.

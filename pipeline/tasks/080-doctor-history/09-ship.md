# Görev 080 — Teslim

`atlas doctor --save-baseline` history + `--history-keep N` + `--history-list`.

## Uygulama

- `_DEFAULT_DOCTOR_HISTORY_DIR = .atlas/doctor-history` sabit.
- `_list_doctor_history()`: `baseline-YYYY-MM-DD.json` dosyaları
  metadata (date desc).
- `_prune_doctor_history(keep)`: name (date lex sıra) retention.
- `_cmd_doctor`:
  - `--save-baseline` default path ile → tarihçe snapshot da yaz
    (custom path → tarihçe YOK).
  - `--history-keep N` verildiyse retention (yeni yazımdan sonra).
  - `--history-list` kısa devre (SPEC 040 `--schema` kalıbı) — sağlık
    kontrolü yapmadan bilgi.
- `_human_bytes_or_fallback` forward-safe helper.
- Parser: `--history-keep N`, `--history-list` bayrakları.

## Kanıt

- +14 test (`tests/test_cli_doctor_history.py`):
  - Birim (6): dizin yok, boş dizin, snapshot metadata, date desc,
    prune keep=1, prune keep=0 hata.
  - CLI (8): default history kopyası, custom path history yok, retention,
    keep 0 exit 2, list boş, list JSON, list kısa devre (sağlık yok),
    save bit-uyumlu.
- 1195 → **1209 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 062 `--save-baseline` default path içerik aynı (yan etki tarihçe
  ek dosya).
- SPEC 057/062 `--diff`/`--auto-baseline` BİT-UYUMLU.

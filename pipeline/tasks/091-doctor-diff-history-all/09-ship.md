# Görev 091 — Teslim

`atlas doctor --diff-history-all [--json]`.

## Uygulama

- `_cmd_doctor` içine SPEC 091 bloğu (SPEC 086 üstünde):
  - MUTEX: `--diff/--auto-baseline/--diff-history/--save-baseline/
    --serve/--format prometheus` → exit 2.
  - `--schema` SPEC 040 kısa devre BİT-UYUMLU (--schema önce çalışır,
    diff-history-all ignored — MUTEX gereksiz).
  - Tarihçe boş → exit 2 + "atlas doctor --save-baseline" öneri.
  - Her snapshot için `_diff_doctor_reports(baseline, report)`.
  - Sıra: date desc (en yeni önce; SPEC 086 kalıbı).
  - Pretty tablo: `date | +warn | -warn | Δquality`.
  - JSON: `{snapshots: [{date, path, delta: {SPEC 057 şeması}}]}`.
- `--save-baseline` mutex listesi güncellendi: `--diff-history-all` de mutex.
- Parser: `--diff-history-all` action="store_true".

## Kanıt

- +10 test (`tests/test_cli_doctor_diff_history_all.py`):
  - Tarihçe boş → exit 2 + öneri.
  - 3 snapshot → tablo 3 satır date desc.
  - `--json` snapshots + SPEC 057 delta anahtarları.
  - MUTEX: --diff, --diff-history N, --save-baseline, --auto-baseline,
    --format prometheus (5 test).
  - --schema BİT-UYUMLU (kısa devre kazanır, SPEC 040).
  - --diff-history-all YOKSA SPEC 021 çıktı AYNI.
- 1302 → **1312 yeşil** (+10), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 057 delta şeması AYNI.
- SPEC 086 `--diff-history N` davranışı AYNI.
- SPEC 021 default doctor AYNI.
- SPEC 040 `--schema` kısa devre AYNI.
- SPEC 062/080 save-baseline/history-list DOKUNULMADI (mutex listesi
  hariç).

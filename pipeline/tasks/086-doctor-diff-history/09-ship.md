# Görev 086 — Teslim

`atlas doctor --diff-history N`.

## Uygulama

- `_cmd_doctor` içine SPEC 086 bloğu (auto-baseline'ın hemen ardından):
  - `--diff-history` + `--diff/--auto-baseline` MUTEX exit 2.
  - `N < 1` → exit 2.
  - Tarihçe boş → exit 2 + "atlas doctor --save-baseline" öneri.
  - `N > len(history)` → exit 2 (mesajda N ve len).
  - Seçilen snapshot path → `diff_baseline_arg` (mevcut `_diff_doctor_reports`
    yolu çalışır — SPEC 057 delta şeması BİT-UYUMLU).
  - Bilgi mesajı stdout: `[--diff-history N] snapshot: <date> (<path>)`.
- `--save-baseline` mutex listesi güncellendi: `--diff-history` de mutex.
- Parser: `--diff-history` type=int default None.

## Kanıt

- +10 test (`tests/test_cli_doctor_diff_history.py`):
  - Tarihçe boş → exit 2 + öneri.
  - N=0 → exit 2.
  - N > len → exit 2.
  - N=1 → en yeni; N=len → en eski.
  - MUTEX: --diff, --auto-baseline, --save-baseline.
  - `--json` SPEC 057 delta anahtarları (warnings_added/removed).
  - `--diff-history` YOKSA SPEC 021 çıktı AYNI.
- 1264 → **1274 yeşil** (+10), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 057 delta şeması AYNI.
- SPEC 021 doctor default davranış AYNI.
- SPEC 062/080 save-baseline/history-list DOKUNULMADI (mutex listesi
  hariç).

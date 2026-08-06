# Görev 130 — Teslim

`atlas-doctor.yml` --diff-history-all --strict gate.

## Uygulama
- Yeni step: `Doctor history regression gate (SPEC 097/130)` (id: `history_gate`).
- Tarihçe kontrolü: `test -d + ls baseline-*.json`.
- Varsa: `atlas doctor --diff-history-all --strict > doctor-history-strict.txt`.
- Yoksa: skip, rc_hist=0 (fail-safe).
- Fail step conditional güncellendi: `rc_hist != '0'` de ekli.
- Upload artifact listesine `doctor-history-strict.txt` eklendi.

## Kanıt
- +4 test; 1516 → **1520 yeşil**.

## Değişmeyen sözleşme
- Mevcut fresh strict + auto-baseline diff step'i DOKUNULMADI.
- SPEC 100 diff-history-all artifact üretimi AYNI.

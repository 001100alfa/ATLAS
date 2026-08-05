# Görev 062 — İhtiyaç

SPEC 057 `atlas doctor --diff BASELINE_JSON` regresyonu tespit eder ama
kullanıcı baseline'ı elle üretmek + saklamak zorunda. CI/scheduled
kalibrasyon için otomatik snapshot yönetimi gerek.

## Kabul

- `atlas doctor --save-baseline [PATH]` — mevcut raporu diske yaz.
  - PATH yoksa: `.atlas/doctor-baseline.json` (git-ignored).
  - Diğer output/mutation mode'larıyla mutex.
- `atlas doctor --auto-baseline` — `--diff` yerine geçer, default path'ten
  oku. Dosya yoksa: bilgi + exit 0 (ilk çalıştırma nazikliği).
- `--auto-baseline` + `--diff` mutex (kaynak belirsiz).
- `--strict + --auto-baseline` → regresyon varsa exit 9 (SPEC 057 bit-uyumlu).

## Risk

- `.atlas/` git-ignored → CI'de her run temiz slate; kullanıcı istiyorsa
  `--save-baseline snapshots/prod.json` gibi kalıcı path.

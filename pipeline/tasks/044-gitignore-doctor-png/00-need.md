# Görev 044 — İhtiyaç

22. tur (b5ce74c, doctor toplu güncelleyici) DOCTOR GUI canlı ekran
görüntüsü `DOCTOR_cmd.png` bıraktı — untracked. İki tur boyunca
`git add -A` bu dosyayı istemsizce staged etti; 23. tur 041.1'de bir
kez amend + rm ile temizledim (bkz DECISIONS 2026-07-31 [HATA]).

Bu dosyayı silmek istemiyoruz — kullanıcının yerelinde debug/rapor
değeri var. Ama commit'e girmeyecek.

## Kabul kriteri

- `.gitignore`'a `DOCTOR_cmd.png` + `DOCTOR_*.png` desenleri.
- `git check-ignore DOCTOR_cmd.png` → 0 (ignored).
- `git status --short` → `DOCTOR_cmd.png` görünmez.
- Kalite kapıları (pytest/mypy/ruff/scan) etkilenmez — mevcut 810
  test yeşil kalır.
- Yeni test YOK (dokümantasyon-benzeri değişiklik).

## Riskli

- Gelecekte gerçekten commit etmek istenirse `git add --force
  DOCTOR_cmd.png` gerekir. Kullanıcı gafla ekleyemez artık.
- `DOCTOR_*.png` deseni geniş — gelecekte doctor GUI test snapshot'ları
  yaparsak (görsel regresyon) explicit `git add -f` gerekecek.

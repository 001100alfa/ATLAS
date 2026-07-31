# Görev 044 — Teslim

`.gitignore`'a DOCTOR_*.png deseni.

## Uygulama

- `.gitignore` sonuna yeni blok (`SPEC 044`):
  ```
  # SPEC 044: DOCTOR GUI ekran görüntüleri — debug/test amaçlı, commit edilmez.
  DOCTOR_cmd.png
  DOCTOR_*.png
  ```

## Kanıtlar

- `git check-ignore -v DOCTOR_cmd.png` → `.gitignore:64:DOCTOR_*.png	DOCTOR_cmd.png`
- `git status --short` → sadece `.gitignore` M; PNG YOK.
- 810 test yeşil (bit-uyumlu — kod dokunulmadı).
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- Tümü — sadece git meta.

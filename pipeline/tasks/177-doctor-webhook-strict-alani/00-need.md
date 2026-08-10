# Görev 177 — İhtiyaç

SPEC 168 `doctor --alert-webhook` payload'ında `strict` alanı yok —
webhook alıcısı --strict modunun kullanılıp kullanılmadığını göremez.
`--strict` ile birlikte aynı bulgu ADIM ATLAYAN (exit 9 → CI/pre-commit
gate) hâline gelir; bu bilgi payload'a taşınmalı.

## Kabul

- SPEC 168 payload'a **yeni alan** `strict` (bool) eklenir
  (SPEC 032.4 alan-ekleme bit-uyumlu):
  ```json
  {
    "alert": "doctor",
    "warnings": [...],
    "quality_warnings": {...},
    "strict": true|false
  }
  ```
- Değer: `bool(getattr(args, "strict", False))`.
- Mevcut alanlar DOKUNULMADI (bit-uyumlu ekleme).
- Test: SPEC 168 mevcut testlerini kırmaz + yeni test `strict=true`
  ve `strict=false` payload'ı doğrular.
- SPEC 032 exit 9 davranışı AYNI (webhook ortogonal — payload'a
  yansıtır sadece).

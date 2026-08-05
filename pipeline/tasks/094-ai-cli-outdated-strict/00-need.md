# Görev 094 — İhtiyaç

SPEC 088 `--outdated` filtre yalın bilgi komutu (exit 0). CI/pre-commit
hook için "outdated var mı?" kararını exit code ile döndürmeli. Şu an
`--outdated` sonucu boş değilse bile exit 0.

## Kabul

- `atlas ai-cli list --outdated --strict`.
- `--strict` **yalnız** `--outdated` ile birlikte anlamlı. Aksi hâlde
  SPEC HATASI exit 2.
- `--outdated --strict` + boş filtre → exit 0 (mevcut).
- `--outdated --strict` + boş DEĞİL → exit 4 (SPEC 032 --strict kalıbı;
  SPEC 042 vault verify --strict kod uyumu).
- Pretty/JSON çıktı BİT-UYUMLU (sadece exit code değişir).
- `--strict` VERİLMEZSE SPEC 088 BİT-UYUMLU (exit 0).

# Görev 077 — İhtiyaç

CLAUDE.md ve DECISIONS.md "Docker YASAK" sözleşmesi belirtiyor ama
mekanik gate yok — kullanıcı gafle `Dockerfile` commit ederse fark
edilmez, "sözleşme değişikliği" olarak sızar. CI + pre-commit iki katlı
gate gerek.

## Kabul

- `.github/workflows/no-docker.yml`:
  - push[main] + PR (path filtresi YOK — her PR gate).
  - `git ls-files` ile arşiv tarafında pattern arama:
    `Dockerfile`, `Dockerfile.*`, `docker-compose.{yml,yaml}`,
    `.dockerignore`.
  - Bulgu → `::error file=X::` GitHub Actions annotation + exit 1.
- Pre-commit hook v4 → v5:
  - Yeni "Kapı 3": `git diff --cached --name-only` regex ile Docker
    staged dosyaları tespit. Bulgu → engel + kullanıcıya çözüm mesajı.
  - Regex: `^(.*/)?(Dockerfile(\..*)?|docker-compose\.ya?ml|\.dockerignore)$`.
- Sözleşme değişirse: CLAUDE.md güncelle + workflow sil + hook bloğu
  sil (3 nokta).

## Risk

- `git ls-files` shallow clone'da (CI default) doğru — tracked dosyalar.
- Pre-commit hook fresh clone'da hook v4 kullanıcıları için `hooks
  install --force` gerekir (SPEC 045/052 kalıbı).

# Görev 056 — İhtiyaç

SPEC 045 pre-commit hook vault verify gate'i geliştirici makinesinde
çalışıyor. Ama PR review'da:
- Geliştirici hook'u install etmediyse (fresh clone / farklı editor)
- Emergency `--no-verify` commit
- Fork PR — hook mevcut kullanıcının değil PR yazarının

vault graf sağlığı **CI'de de** doğrulanmalı — reviewer bulguları
elle takip etmesin.

## Kabul kriteri

- `.github/workflows/vault-health.yml` GitHub Actions workflow.
- Tetikleyici:
  - `push` main + vault/src path filtresi
  - `pull_request` + aynı path filtresi
- Job `verify`: ubuntu-latest, timeout-minutes: 5.
- Adımlar:
  1. `actions/checkout@v4`
  2. `astral-sh/setup-uv@v3` (Python paket yöneticimiz)
  3. `uv sync --frozen --extra dev`
  4. `atlas vault verify --strict --dump-report health.md`
     (`continue-on-error: true`; rc `$GITHUB_OUTPUT`'a yazılır)
  5. `actions/upload-artifact@v4` (`health.md`; 30 gün retention)
  6. `peter-evans/create-or-update-comment@v4` — YALNIZ PR + fail'de
  7. Fail step: rc != 0 ise `exit 1` (job'ı fail et)
- `permissions`: `contents: read`, `pull-requests: write`.
- `concurrency`: aynı ref'in eş zamanlı koşumlarını iptal et.

## Riskli

- Fork PR'larda `pull-requests: write` izni yok (GitHub güvenlik
  politikası). Fork'lardan PR açan katkıcılar comment göremez ama
  artifact ve job status'u yine erişilebilir.
- `peter-evans/create-or-update-comment` `comment-id` verilmediğinde
  YENİ comment üretir (aynı PR'a tekrar tekrar). Comment "sürüklenmesi"
  olur ama silme/edit için ekstra karmaşıklık YAGNI — kullanıcı
  isterse artifact'ı indirir.
- `uv.lock` senkron olmalı (`uv sync --frozen`). PR uv.lock değişikliği
  içermiyorsa mevcut lock'la kurulum yapılır.

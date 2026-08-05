# Görev 082 — İhtiyaç

Repo'da 5 workflow var (ci, atlas-doctor, atlas-metrics, vault-health,
no-docker). README'de tek badge yok — yeni katılan görenler CI
durumunu tespit edemez.

## Kabul

- `tools/scripts/gen_ci_badges.py`:
  - `.github/workflows/*.yml` içindeki `name:` alanlarını topla.
  - README'de `<!-- ci-status:start -->` ve `<!-- ci-status:end -->`
    markörleri arasına markdown tablo yerleştir.
  - Marker yok → README sonuna ekle.
  - `--check` bayrağı: drift kontrol (değişiklik varsa exit 1).
  - `--repo OWNER/REPO` bayrağı; env `GITHUB_REPOSITORY` override.
- `.github/workflows/ci-status.yml`:
  - push[main]+PR, workflow YAML veya script değişikliği path filtresi.
  - Script `--check` çalıştır → drift → PR comment + exit 1.
  - Timeout 2dk (küçük iş).

## Risk

- Fresh workflow eklendiğinde kullanıcı `python tools/scripts/
  gen_ci_badges.py` çalıştırmalı + commit. CI gate hatırlatır.
- Script Türkçe mesajları ASCII-only (SPEC 057 cp1254 kalıbı).

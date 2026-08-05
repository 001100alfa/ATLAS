# Görev 082 — Teslim

`ci-status.yml` + README badge tablosu drift gate.

## Uygulama

- `tools/scripts/gen_ci_badges.py`: workflow YAML'lerinden `name:`
  regex ile çek; markdown tablo; `<!-- ci-status:start -->` marker'lar
  arası yaz. `--check` drift kontrol; `--repo OWNER/REPO` + env
  `GITHUB_REPOSITORY` override.
- `.github/workflows/ci-status.yml`: push[main]+PR path filtresi
  (`workflows/**.yml` + script). `python tools/scripts/gen_ci_badges.py
  --check` → drift → PR comment + exit 1. Timeout 2dk.
- README güncellendi (6 workflow badge: atlas-doctor, atlas-metrics,
  ci, ci-status, no-docker, vault-health).

## Kanıt

- +8 test (`tests/test_gen_ci_badges.py`):
  - Script mevcut.
  - --check mod repo güncel (exit 0).
  - README marker'ları mevcut.
  - README tüm 5 workflow badge içerir.
  - --check drift tespit (sahte workflow ekle → exit 1).
  - ci-status.yml YAML valid + `gen_ci_badges.py --check` çağrısı +
    `exit 1`.
  - `--repo` bayrağı env override kabul.
  - Script idempotent (iki çağrı → aynı README).
- 1163 → **1171 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- Diğer workflow'lar BİT-UYUMLU (ci-status okur, değiştirmez).
- README'de mevcut içerik korunur (marker'lar arası salt-değişim).

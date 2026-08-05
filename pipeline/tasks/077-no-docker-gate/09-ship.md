# Görev 077 — Teslim

`no-docker.yml` + pre-commit hook v5 Docker YASAK gate.

## Uygulama

- `.github/workflows/no-docker.yml`: push[main]+PR, `git ls-files`
  pattern arama, bulgu → `::error file=X::` + exit 1.
- `tools/hooks/pre-commit` v4 → v5: yeni "Kapı 3" Docker gate.
  Regex `^(.*/)?(Dockerfile(\..*)?|docker-compose\.ya?ml|\.dockerignore)$`.
- `_HOOK_SIGNATURE` `v4 → v5`.

## Kanıt

- +5 hook testi (SPEC 077):
  - `_HOOK_SIGNATURE == "# atlas-hook v5"`.
  - Şablon v5 imzalı.
  - Docker YASAK bloğu içerir (SPEC 077, patterns).
  - Docker bloğu Kapı 1 + 2'den sonra sıralı.
  - (+ mevcut 29 hook testi v5'e uyumlu güncellendi).
- +5 workflow testi (SPEC 077):
  - YAML valid + name.
  - Tetikleyiciler push+PR (path filtresi yok).
  - Run zinciri `git ls-files` + patterns + exit 1.
  - Timeout ≤ 5dk.
  - Repo tracked artefakt YOK (`git ls-files` semantik doğrulama).
- 1110 → **1117 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 034/045/052 hook zinciri BİT-UYUMLU (yeni Kapı 3 ek).
- Kurulu v4 hook'lar `hooks status`'ta `up_to_date=False`; kullanıcı
  `hooks install --force` ile v5'e geçer.

# Görev 088 — Teslim

`atlas ai-cli list --outdated [--json]`.

## Uygulama

- `_strip_semver_prefix(spec)`: `^`, `~`, `>=`, `>`, `=`, `*`, boşluk
  sıyır (basit prefix; npm semver-satisfies DEĞİL — dok. 088).
- `_cmd_ai_cli_list`: `outdated=True` ise filtre:
  `installed is None` VEYA `_strip_semver_prefix(expected) != installed`.
- `--outdated` VERİLMEZSE davranış SPEC 037.2 BİT-UYUMLU.
- Pretty başlık: `... — outdated`; boş → `(guncelleme yok)`.
- Parser: `--outdated` action="store_true".

## Kanıt

- +8 test (`tests/test_cli_ai_cli_list_outdated.py`):
  - `_strip_semver_prefix` birim.
  - `installed is None` → outdated.
  - `stripped != installed` → outdated.
  - Hepsi güncel → boş `packages` + pretty `(guncelleme yok)`.
  - `--outdated` VERİLMEZSE tam liste.
  - Pretty çıktı sadece outdated satırlar.
  - `AI_CLI_DIR` yok → exit 2.
  - Bozuk `package.json` → exit 2.
- 1229 → **1237 yeşil** (+8), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 037.2: `--outdated` YOK ise davranış AYNI.
- Diğer ai-cli komutları etkilenmedi.

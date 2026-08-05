# Görev 094 — Teslim

`atlas ai-cli list --outdated --strict`.

## Uygulama

- `_cmd_ai_cli_list`: `strict_mode` + not `outdated_mode` → SPEC HATASI
  exit 2 (ön-kontrol).
- `outdated_mode and strict_mode and packages` → `exit_rc = 4`.
- JSON çıktı: filtreli packages basılır, ama return exit_rc (4/0).
- Pretty çıktı: satırlar basılır; exit 4 ise "SAĞLIK BAŞARISIZ: --strict
  verildi, N paket outdated" stderr.
- Parser: `--strict` action="store_true".

## Kanıt

- +6 test (`tests/test_cli_ai_cli_outdated_strict.py`):
  - Hepsi güncel + --outdated --strict → exit 0 + "(guncelleme yok)".
  - Outdated var + --strict → exit 4 + "SAĞLIK BAŞARISIZ" stderr.
  - JSON + --strict + bulgu → exit 4, JSON packages yazılır.
  - --strict tek başına (outdated yok) → SPEC HATASI exit 2.
  - --outdated (strict yok) + bulgu → exit 0 (SPEC 088 BİT-UYUMLU).
  - Yalın `ai-cli list` → SPEC 037.2 exit 0.
- 1284 → **1290 yeşil** (+6), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 037.2: yalın `list` DAVRANIŞI AYNI.
- SPEC 088: `--outdated` (strict yok) exit 0 AYNI; filtre AYNI.
- Exit 4 kalıbı SPEC 042 vault verify --strict ile UYUMLU.

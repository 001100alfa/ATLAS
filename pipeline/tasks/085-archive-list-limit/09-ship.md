# Görev 085 — Teslim

`atlas archive --list --sort-by KEY [--desc] --limit N`.

## Uygulama

- `_cmd_archive_list`: sıralamadan SONRA `entries = entries[:limit]`.
- `limit is None` → dokunma (SPEC 075/079 BİT-UYUMLU).
- `limit <= 0` → SPEC HATASI exit 2 ("--limit N > 0 olmalı").
- `limit > len(entries)` → tüm liste (kesme yok, hata yok).
- Parser: `--limit` type=int default None (opsiyonel).

## Kanıt

- +8 test (`tests/test_cli_archive_list_limit.py`):
  - top-N sıralamadan sonra (size --desc --limit 2).
  - default name alfabetik + --limit 2.
  - limit > len → tam liste.
  - limit 0 → exit 2 + SPEC HATASI mesajı.
  - limit negatif → exit 2.
  - --limit yoksa BİT-UYUMLU (SPEC 075/079).
  - Pretty (non-JSON) çıktı da --limit uyar.
  - --limit 1 members --desc → tek en büyük.
- 1221 → **1229 yeşil** (+8), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 075/079: `--limit` VERİLMEZSE davranış AYNI.
- Diğer archive komutları etkilenmedi.

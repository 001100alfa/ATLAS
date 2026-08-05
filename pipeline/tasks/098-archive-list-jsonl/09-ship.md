# Görev 098 — Teslim

`atlas archive --list --json-lines [sort/limit/name-match zinciri]`.

## Uygulama

- `_cmd_archive_list`: sıralama/limit/filter zinciri sonrası
  `jsonl_mode` dalı.
- MUTEX: `--json` + `--json-lines` → exit 2.
- Her entry: SPEC 075 alanlarıyla AYNI (`archive`, `task_id`, `date`,
  `size_bytes`, `size_human`, `member_count`, `mtime`).
- Son satır: `{"type":"summary","archive_root":..,"count":N}`.
- Boş sonuç → yalnız summary (count=0).
- Parser: `--json-lines` action="store_true".

## Kanıt

- +7 test (`tests/test_cli_archive_list_jsonl.py`):
  - 3 arşiv + summary satır sayısı.
  - Arşiv alanları SPEC 075 ile AYNI.
  - Boş dizin → summary count=0.
  - --json + --json-lines MUTEX exit 2.
  - --sort-by --desc --limit ile en büyük 2 doğru.
  - --name-match filtre uygulanır.
  - --json-lines YOKSA --json bit-uyumlu (tek dizi).
- 1328 → **1335 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 075/079/085/093 mevcut davranışları AYNI (`--json`, pretty).
- Filter/sort/limit zinciri stream öncesi (deterministik sıra).

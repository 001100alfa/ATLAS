# Görev 079 — Teslim

`atlas archive --list --sort-by KEY [--desc]`.

## Uygulama

- `_cmd_archive_list`: `key_map = {name, size, date, members}`
  fonksiyon dict; `sorted(entries, key=..., reverse=desc)`.
- `date` boşsa mtime fallback (atipik format arşivler için).
- `member_count=-1` (bozuk tar) → 0 kabul (sort'ta sona düşer).
- Parser: `--sort-by` choices + `--desc` bayrak.

## Kanıt

- +8 test:
  - Default `name` bit-uyumlu (alfabetik).
  - --sort-by size (küçükten büyüğe) + --desc (büyükten).
  - --sort-by date (YYYY-MM-DD sıralı).
  - --sort-by members.
  - Geçersiz choice → argparse SystemExit(2).
  - --desc name ile ters sıra.
  - İnsan çıktısı da sıralı (bbb > aaa).
- 1171 → **1179 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 075 default `name` alfabetik BİT-UYUMLU.
- Diğer archive komutları etkilenmedi.

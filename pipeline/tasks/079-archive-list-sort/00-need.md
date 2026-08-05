# Görev 079 — İhtiyaç

SPEC 075 `--list` alfabetik sıralı. Kullanıcı "en büyük 3 arşiv"
veya "en yeni tarih" görmek isterse `--json | jq` gerek. Doğal
sıralama bayrağı yok.

## Kabul

- `atlas archive --list --sort-by {name,size,date,members} [--desc]`.
- Default `name` (SPEC 075 alfabetik BİT-UYUMLU).
- `size` → `size_bytes` (küçükten büyüğe).
- `date` → `date` alanı (`YYYY-MM-DD`); boşsa mtime fallback.
- `members` → `member_count` (bozuk tar `-1` → 0 kabul).
- `--desc` ters sıra.
- Geçersiz choice → argparse SystemExit(2).

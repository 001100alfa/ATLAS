# Görev 115 — İhtiyaç

SPEC 075 `--json` tek JSON dizisi stdout'a. SPEC 105 `--json-lines --out`
mevcut ama düz JSON için `--out` yok. Sadece `--json` (dizi) kullanan
tüketiciler için `--out PATH` bayrağı gerek.

## Kabul

- `atlas archive --list --json --out PATH`.
- `--out` mevcut YOL: `--json-lines` ile birlikte OR `--json` ile birlikte
  (SPEC 105/115 birleşimi).
- Parent auto-mkdir; IO hatası exit 2.
- Dosya içeriği stdout `--json` modu ile BİT-UYUMLU (tek JSON dizisi).
- `--out` + hem yok (`--json-lines` yok VE `--json` yok) → exit 2.
- Diğer bayraklar (sort/limit/name-match) ORTOGONAL.

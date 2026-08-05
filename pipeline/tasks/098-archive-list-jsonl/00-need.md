# Görev 098 — İhtiyaç

SPEC 075/079/085/093 `archive --list --json` tüm arşiv metadata'sını
tek büyük dizi olarak basar. Yüzlerce arşiv olan üretim kurulumunda
streaming NDJSON tüketici (jq, python line-by-line) uygun.

## Kabul

- `atlas archive --list --json-lines [--sort-by KEY] [--desc]
  [--limit N] [--name-match PATTERN]`.
- Her arşiv tek satır: `{"archive","task_id","date","size_bytes",
  "size_human","member_count","mtime"}` (SPEC 075 alanları AYNI).
- Son satır özet: `{"type":"summary","archive_root":..,"count":N}`.
- `--json-lines` + `--json` MUTEX exit 2.
- Diğer bayraklar (`--sort-by/--desc/--limit/--name-match`) ORTOGONAL
  (filter → sort → limit → stream).
- Boş sonuç → sadece summary satırı (count=0).
- `--json-lines` YOKSA SPEC 075/079/085/093 BİT-UYUMLU.

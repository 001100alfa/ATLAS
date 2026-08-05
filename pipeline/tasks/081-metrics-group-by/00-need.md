# Görev 081 — İhtiyaç

SPEC 076 `--window MINUTES` filtre; ama gruplandırma yok. "Bugünün her
saati kaç token" veya "geçen haftanın her günü toplam cost" için
`--group-by hour|day` doğal tamamlama.

## Kabul

- `atlas metrics --group-by {hour,day} [--window MINUTES] [--json]`.
- ts alanı ISO 8601 parse; `hour` → `YYYY-MM-DDTHH`, `day` → `YYYY-MM-DD`.
- ts yok/bozuk kayıt → `"unknown"` grup (sona).
- Deterministik sıra (ISO lex = kronolojik).
- Grup dict: `{key, records, tokens_in, tokens_out, cache_creation, cache_read}`.
- `--group-by` + `--format prometheus` → exit 2 (semantik mutex).
- `--group-by` + `--alert` → exit 2 (semantik mutex; alert tekil değer).
- `--window` ile ORTOGONAL (önce window filtre, sonra group).

## Risk

- Grup çıktısı `cost` içermez (fiyat env dependency + group başına
  hesap YAGNI); kullanıcı ham token'larla dış hesap yapar.

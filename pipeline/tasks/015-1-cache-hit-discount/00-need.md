# 015.1 — İhtiyaç: cache-hit token indirimi

## Bağlam
SPEC 011 anthropic response `usage.input_tokens`+`output_tokens`
alanlarını yakaladı. SPEC 015 `cache_control: ephemeral` ile sistem
promptu 5 dk cache'leniyor. Anthropic response'ta cache tetiklendiğinde
`usage` alanı ek iki alan taşır:

- `cache_creation_input_tokens`: cache oluşturulan (**tam fiyat + %25**)
- `cache_read_input_tokens`: cache'ten okunan (**%10 fiyat**)
- `input_tokens`: normal (tam fiyat)

Şu an ATLAS bu ayrımı yok sayıyor — cache'li çağrılar tam fiyat gibi
görünüyor. Görev 013 `charge_tokens` ve Görev 011 trace fatura tahmini
verirken **cache indirimi göz ardı ediliyor**, kullanıcı yanlış cost
görüyor.

## İhtiyaç (tek cümle)
`_extract_usage` cache alanlarını da yakalasın; `_fmt_cost` ve
`CallBudget.charge_tokens` cache-read'i `price_in * 0.1`, cache-creation'ı
`price_in * 1.25` ile hesaplasın; trace format bilgi taşısın:
`in=N (cache=Y r=Z) out=M`.

## Ölçülebilir Başarı
- **M1 — Usage yapısı genişlemesi:** `_extract_usage(data)` artık
  4-tuple `(input, output, cache_creation, cache_read)` döner
  (11'de 2-tuple idi).
- **M2 — Fiyat sabitleri:** `_CACHE_READ_MULT = 0.1`,
  `_CACHE_WRITE_MULT = 1.25` — Anthropic kamu tarifesi. Sabitler
  modülde net.
- **M3 — Cost formülü:** `cost = input * p_in / 1e6 + cache_creation
  * p_in * 1.25 / 1e6 + cache_read * p_in * 0.1 / 1e6 + output *
  p_out / 1e6`. Cache alanları 0 → 011 davranışı bit-uyumlu.
- **M4 — Trace format:** `[llm] anthropic tokens: in=N (cache=W r=R)
  out=M cost≈$X.XXXXXX`. Cache=0 hem write hem read yoksa parantez
  atlanır (`in=N out=M`).
- **M5 — `CallBudget.charge_tokens` genişlemesi:** yeni imza
  `charge_tokens(input_tokens, output_tokens, price_in, price_out,
  *, cache_creation=0, cache_read=0)`. Eski çağrılar
  (`charge_tokens(a, b, c, d)`) bit-uyumlu — yeni kwargs default 0.
- **M6 — Test:** +5 test — cache-read %10, cache-write %25 fazla,
  ikisi bir arada, trace format cache'siz vs cache'li, `_extract_usage`
  4-tuple.
- **M7 — DECISIONS:** [KARAR] neden Anthropic tarife sabitleri kodda;
  cache alanları neden default 0.

## Kapsam DIŞI
- claude/acp backend'ler — usage native değil (011 kapsamı).
- Model-özel cache fiyatı (opus vs haiku ayrımı) — env yeter.
- 1h cache TTL (`type: "1h"`) — YAGNI.

## Kısıt
- `_extract_usage` iç fonksiyon; imza genişleyebilir.
- `CallBudget.charge_tokens` — yeni parametreler **keyword-only +
  default=0** → 013 mevcut çağrıları etkilenmez.
- `_fmt_cost` yeni imza `(in, out, cache_c=0, cache_r=0)`.
- Türkçe mesaj; ruff/mypy temiz.

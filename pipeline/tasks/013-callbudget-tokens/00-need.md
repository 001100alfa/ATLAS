# 013 — İhtiyaç: CallBudget'a token maliyeti entegrasyonu

## Bağlam
SPEC 011 anthropic response `usage.input_tokens`+`output_tokens`
alanlarını yakalayıp `ATLAS_LLM_TRACE=1` ile stderr'a rapor etti.
Ancak bu bilgi CallBudget'a **hiç yansımıyor** — soyut kredi modeli
yalnız `act()` cost'unu görür, LLM plan çağrılarının gerçek maliyeti
görünmez. Sonuç: yüksek maliyetli bir görev bütçe içinde görünürken
Anthropic panelinde büyük bir fatura üretiyor olabilir.

## İhtiyaç (tek cümle)
`CallBudget.charge_tokens(input_tokens, output_tokens, price_in, price_out)`
metodu ile anthropic çağrılarının cost'u da bütçeye düşsün; aşarsa
`BudgetExceededError`. run_loop mevcut kalıbı korunur.

## Ölçülebilir Başarı
- **M1 — CallBudget sözleşmesi genişlemesi:** yeni public method
  `charge_tokens(in_tok, out_tok, price_in, price_out)`. Cost = `in *
  price_in / 1e6 + out * price_out / 1e6` (mevcut `_fmt_cost` kalıbı,
  per million USD). Bütçe aşarsa `BudgetExceededError` (mevcut sınıf).
- **M2 — Mevcut `charge()` değişmez:** `run_loop` içindeki
  `budget.charge(cost, what)` çağrısı **aynen** çalışır. `charge_tokens`
  ayrı yol.
- **M3 — Fiyat=0 no-op:** `price_in=0 and price_out=0` → cost 0,
  bütçe hiç değişmez. Env yoksa fiyat 0 sayılır (011 fail-safe
  kalıbıyla simetrik).
- **M4 — Anthropic backend entegrasyonu:** `_call_anthropic`
  imzasına opsiyonel `on_usage: Callable | None = None` callback
  eklenir. Response usage varsa `on_usage(in_tok, out_tok)` çağrılır.
  `_anthropic_planner` closure'ına `budget.charge_tokens` bind edilir.
- **M5 — Fabrika-imza değişmez:** `_anthropic_planner(goal, context)`
  imzası **korunur** — budget referansı `context` gibi yeni bir
  keyword-only ile geçer. Aslında en temiz yaklaşım: `_anthropic_planner`
  içinde `on_usage` kabul et; fabrika-çağıran `cli.py` bind eder.
- **M6 — Fiyat okuma:** Fabrika `ATLAS_LLM_PRICE_IN/OUT` env'ini
  aynı `_fmt_cost` gibi okur (parse hatası → 0). Böylece 011 fiyat
  env'iyle aynı kaynaktan çekilir.
- **M7 — Trace korunur:** `ATLAS_LLM_TRACE=1` stderr çıktısı
  değişmez — usage hem charge hem trace edilir.
- **M8 — claude/acp değişmez:** iki backend usage yayınlamıyor,
  charge_tokens çağırmıyor. run_loop davranışı aynı.
- **M9 — Test:** CallBudget birim test (+3), anthropic entegrasyon
  test (+3 — happy, no-price no-op, aşım BudgetExceededError).
  Coverage ≥ %90.
- **M10 — DECISIONS:** [KARAR] `charge_tokens` neden ayrı;
  callback yaklaşımı; fiyat 0 no-op.

## Kapsam DIŞI
- CallBudget'a token limiti (input_max/output_max) — kredi tek
  boyut yeter.
- claude/acp usage yayını — protokolde native değil (kapsam DIŞI).
- Prompt caching indirimi — Görev 015 ile birleşir (fiyat model
  ayrımı orada gelir).
- Cache-hit token'ı ayrı ücretlendirme — 015+.

## Kısıt
- `CallBudget` (dataclass) — mevcut alanlar korunur; yeni method
  eklenir.
- `_call_anthropic` — mevcut positional/keyword parametreler korunur;
  yeni **keyword-only default=None** callback.
- `BudgetExceededError` mevcut sınıf; yeni exception yok.
- Türkçe hata mesajı.

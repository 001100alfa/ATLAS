# 015.1 — Ship

## Sonuç
Anthropic prompt caching aktifken (`Goal.prompt_cache=true`) response
`usage` alanında dönen `cache_creation_input_tokens` (%125 fiyat) ve
`cache_read_input_tokens` (%10 fiyat) alanları hem trace hem
`CallBudget.charge_tokens`'a doğru fiyatla yansıyor.

- Sabitler: `_CACHE_READ_MULT = 0.1`, `_CACHE_WRITE_MULT = 1.25`.
- `_extract_usage` **4-tuple** döner: `(input, output, cache_c, cache_r)`.
- `_fmt_cost(in, out, cache_c=0, cache_r=0)` — cache indirimi/primi.
- Trace format: cache alanları varsa `in=N (cache=W r=R) out=M`;
  yoksa 011 formatı bit-uyumlu (`in=N out=M`).
- `on_usage` callback imzası `(int, int, int, int)` — cache alanları
  da geçer. CLI `_on_usage` 4-arg alır ve `charge_tokens(...,
  cache_creation=cache_c, cache_read=cache_r)` çağırır.
- `CallBudget.charge_tokens` yeni **keyword-only** parametreler
  `cache_creation: int = 0`, `cache_read: int = 0` — 013 mevcut
  çağrıları bit-uyumlu.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +_CACHE_*_MULT sabitleri,
                                            _extract_usage 4-tuple,
                                            _fmt_cost cache paramları,
                                            _emit_anthropic_usage_trace cache format,
                                            _call_anthropic on_usage 4-arg,
                                            _anthropic_planner/make_planner tip güncelleme)
src/atlas_core/orchestrator/core.py       (edit: CallBudget.charge_tokens
                                            cache_creation/cache_read kwargs)
src/atlas_core/cli.py                     (edit: _on_usage 4-arg)
tests/test_callbudget_tokens.py           (+5 test — cache_read %10,
                                            cache_creation %125, hepsi bir arada,
                                            013 uyumlu default, what mesajı)
tests/test_planner_anthropic.py           (+5 test — _extract_usage 4-tuple,
                                            cache yok 0, trace cache format,
                                            trace cache yok eski format,
                                            on_usage cache alanları)
tests/test_planner_anthropic.py           (edit: 013 testleri 4-arg lambda'ya
                                            güncellendi — captured 4-tuple)
pipeline/tasks/015-1-cache-hit-discount/*.md (5 artefakt)
```

## Sözleşme değişmezliği
- `CallBudget.charge_tokens` yeni parametreler **keyword-only +
  default=0** → 013 çağrıları etkilenmedi (testler yeşil).
- `_call_anthropic`, `_anthropic_planner`, `make_planner` `on_usage`
  tipi genişledi (2-arg → 4-arg); 013 testleri güncellendi. Bu
  **iç API** — public sözleşme (planner Callable) değişmedi.
- `_extract_usage` iç fonksiyon; imza genişleyebilir.

## Kalite kapıları
- pytest: **454 passed** (444 → +10)
- mypy strict + ruff: temiz

## Branch
`feat/015.1-cache-hit-discount` — main üstünde tek commit.

## Kullanım örneği
```yaml
# YAML aynı — cache_control 015'ten
llm_prompt: |
  Sen kıdemli mühendissin. <uzun persona>
prompt_cache: true
```
```bash
# Fiyat env verilirse cache indirimi bütçeye ve stderr trace'e yansır
export ATLAS_LLM_PRICE_IN=3
export ATLAS_LLM_PRICE_OUT=15
export ATLAS_LLM_TRACE=1
# Cache-hit senaryosunda:
#   [llm] anthropic tokens: in=50 (cache=0 r=1200) out=45 cost≈$0.001110
```

## Notlar
- Anthropic tarife çarpanları **modül sabitleri**; model-özel
  değil (Sonnet/Opus aynı oran). Anthropic tarife değişirse buradan
  güncellenir.
- 013 mevcut testleri güncellendi (2 test) — `on_usage` 4-arg lambda
  ile çağrılıyor.

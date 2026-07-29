# 013 — Ship

## Sonuç
`CallBudget.charge_tokens(input_tokens, output_tokens, price_in, price_out)`
metodu eklendi; anthropic backend usage'ı bu metoda beslenir ve LLM
maliyeti kredi cinsinden bütçeye düşer. Aşarsa `BudgetExceededError`
(mevcut sınıf).

- `_call_anthropic(..., on_usage: Callable | None = None)` — response
  usage'ı callback'e verir (keyword-only, default None).
- `_anthropic_planner(..., on_usage=...)` — closure'a bind.
- `make_planner(..., on_usage=...)` — anthropic dallanmasına iletir;
  diğer backend'lerde parametre yok sayılır.
- CLI `_cmd_run_goal`: `_read_llm_prices()` env'inden fiyat + `_on_usage
  = budget.charge_tokens` bind.
- `_extract_usage(data)` yardımcısı 011 trace ve 013 charge tarafından
  paylaşılır (tek yerde parse).

Fiyat env'i yoksa/negatifse `charge_tokens` **no-op** (011 fail-safe
kalıbıyla simetrik); bütçe hiç değişmez — geriye uyumlu.

## Dosyalar
```
src/atlas_core/orchestrator/core.py       (edit: CallBudget.charge_tokens)
src/atlas_core/orchestrator/planner.py    (edit: _extract_usage,
                                            _call_anthropic on_usage,
                                            _anthropic_planner on_usage,
                                            make_planner on_usage)
src/atlas_core/cli.py                     (edit: +_read_llm_prices,
                                            _cmd_run_goal on_usage bind)
tests/test_callbudget_tokens.py           (yeni, 9 test)
tests/test_planner_anthropic.py           (+3 test — on_usage happy,
                                            None no-op, budget aşımı iletilir)
pipeline/tasks/013-callbudget-tokens/*.md (5 artefakt)
```

## Sözleşme değişmezliği
- `CallBudget` mevcut alanlar korundu; `charge()` sözleşmesi aynen
  çalışır — sadece yeni `charge_tokens` metodu.
- `Planner`, `run_loop`, `BudgetExceededError` — dokunulmadı.
- `make_planner` yeni parametre **keyword-only + default=None** →
  eski çağrılar (mevcut testler) etkilenmez.
- `_call_anthropic`, `_anthropic_planner` de aynı garanti.

## Kalite kapıları
- pytest: **419 passed** (407 → +12)
- mypy strict + ruff: temiz

## Branch
`feat/013-callbudget-tokens` — main üstünde tek commit.

## Bekleyen (kapsam DIŞI)
- Prompt caching indirimi — Görev 015 fiyat model ayrımı.
- Cache-hit token'ı ayrı ücretlendirme — 015+.
- claude/acp backend usage yayını — protokol native değil.

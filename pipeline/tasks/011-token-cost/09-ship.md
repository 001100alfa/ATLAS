# 011 — Ship

## Sonuç
Anthropic response `usage.input_tokens` + `output_tokens` yakalanır ve
`ATLAS_LLM_TRACE=1` env'inde stderr'a rapor edilir:

```
[llm] anthropic tokens: in=1234 out=456 cost≈$0.010680
```

Fiyat hesabı opsiyonel: `ATLAS_LLM_PRICE_IN` + `ATLAS_LLM_PRICE_OUT`
(per million token, USD) verilirse cost hesaplanır; yoksa/bozuksa
`cost≈?` (fail-safe — çağrı bozulmaz).

**Rapor-only:** CallBudget'a token yansıması YOK; soyut kredi modeli
korundu. Görev 013 gerçek token→bütçe dönüşümünü ele alacak.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +_emit_anthropic_usage_trace
                                            + _fmt_cost; _call_anthropic
                                            sonda çağırır)
tests/test_planner_anthropic.py           (+5 test — trace açık/kapalı,
                                            cost hesabı, usage yok,
                                            fiyat env bozuk)
pipeline/tasks/011-token-cost/*.md        (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_anthropic`, `_anthropic_planner`, `Planner`, `make_planner` —
  hepsi dokunulmadı imzada.
- Yalın yan-etki: `sys.stderr` yazımı, env kapalıysa no-op.
- claude/acp backend'ler değişmez (usage native değil).

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM_TRACE=1` | Trace + usage stderr'a (008 ile aynı env; retry'e ek olarak usage) |
| `ATLAS_LLM_PRICE_IN` | Anthropic input fiyat, per million USD (ops.) |
| `ATLAS_LLM_PRICE_OUT` | Anthropic output fiyat, per million USD (ops.) |

## Kalite kapıları
- pytest: **402 passed** (397 → +5)
- mypy strict + ruff: temiz

## Branch
`feat/011-token-cost` — 010 üstünde tek commit.

## Bekleyen (013 rezerv)
- CallBudget'a token→kredi dönüşümü
- Otomatik quota kesme (bütçe aşımı → sıradaki plan çağrısı iptal)
- Anthropic prompt caching indirimi
- Model-specific fiyat tablosu (env yerine sabit + override)

# 019 — Ship

## Sonuç
`Goal.stream: bool = False` opsiyonel alanı eklendi. True olduğunda
Anthropic Messages API request'ine `stream: true` eklenir; response
SSE olarak parse edilir; `content_block_delta` `text_delta`
event'lerindeki metin biriktirilir; **ilk newline gelince kesilir**
ve bağlantı kapatılır. Algılanan gecikme düşer.

- Non-streaming yol (varsayılan) **bit-uyumlu** korundu — 011/013/015.1
  tüm testleri yeşil.
- `message_start` ve `message_delta` içindeki `usage` yakalanır —
  013 (charge_tokens) + 011 (trace) doğal uyum.
- Erken kesme (`resp.close()`) sonrası son delta'lar okunmaz —
  gerçek hız kazancı.
- Hata dallanması: geçersiz SSE JSON → `LLMPlannerError`; boş stream
  → boş plan hatası; HTTPError yolları streaming'te de aynı.

## Dosyalar
```
src/atlas_core/orchestrator/goals.py      (edit: +Goal.stream alanı + load kolu)
src/atlas_core/orchestrator/planner.py    (edit: _call_anthropic stream keyword,
                                            +_read_anthropic_stream SSE parser,
                                            _anthropic_planner goal.stream bind)
tests/test_goals.py                       (+3 test — alan yok/true/tip)
tests/test_planner_anthropic.py           (+5 test — happy erken kes,
                                            non-streaming yol, boş, usage,
                                            geçersiz SSE)
pipeline/tasks/019-anthropic-streaming/*.md (5 artefakt)
```

## Sözleşme değişmezliği
- `Goal` yeni alan son sırada + default'lu (003.2 kalıbı).
- `_call_anthropic` yeni parametre **keyword-only + default=False**
  → eski çağrılar etkilenmez.
- `_anthropic_planner`, `make_planner` imzaları korundu.
- claude/acp backend'ler değişmez.

## Kalite kapıları
- pytest: **477 passed** (469 → +8)
- mypy strict + ruff: temiz

## Branch
`feat/019-anthropic-streaming` — 018 üstünde tek commit.

## Kullanım örneği
```yaml
goal: "büyük dosyayı çöz"
plan_kind: llm
llm_prompt: |
  Sen kıdemli mühendissin.
stream: true    # ilk plan satırında kes → algılanan gecikme düşer
```

## Bekleyen
- `input_json_delta` tool-use deltaları — 016.1+ ile birlikte.
- Async iterator API — YAGNI (subprocess/urllib blocking yeter).

# 015 — Ship

## Sonuç
`Goal.prompt_cache: bool = False` opsiyonel alanı eklendi. True olduğunda
+ `goal.llm_prompt` set edilmişse anthropic body.system alanı **bloklar
listesi** formatına döner ve `cache_control: {"type": "ephemeral"}`
taşır. Sonuç: sistem promptu 5 dakika model tarafında cache'lenir —
tekrarlı çağrılarda hız + maliyet indirimi.

- Alan yoksa/False → system string (010 davranışı, bit-uyumlu).
- True + llm_prompt yok → system alanı hiç gönderilmez (cache tek
  başına anlamsız).
- claude/acp backend'ler alanı yok sayar (protokolde native değil).

## Dosyalar
```
src/atlas_core/orchestrator/goals.py      (edit: +prompt_cache alanı + load kolu)
src/atlas_core/orchestrator/planner.py    (edit: _call_anthropic system tipi
                                            genişletildi (str|list[dict]|None);
                                            _anthropic_planner cache dallanması)
tests/test_goals.py                       (+4 test — alan yok/true/false/tip)
tests/test_planner_anthropic.py           (+3 test — cache kapalı string,
                                            açık bloklar, açık ama prompt yok)
pipeline/tasks/015-anthropic-cache/*.md   (5 artefakt)
```

## Sözleşme değişmezliği
- `Goal` yeni alan son sırada + default'lu (003.2 kalıbı).
- `Planner`, `make_planner`, `_anthropic_planner` imzaları korundu.
- `_call_anthropic` `system` parametresi `str | list[dict] | None`
  olarak genişledi ama **keyword-only + default None** → mevcut
  çağrılar etkilenmez.

## Kalite kapıları
- pytest: **437 passed** (430 → +7)
- mypy strict + ruff: temiz

## Branch
`feat/015-anthropic-cache` — 014 üstünde tek commit.

## Kullanım örneği
```yaml
goal: "kesit hesabı yap"
plan_kind: llm
llm_prompt: |
  Sen EN 1993'e hakim yapı mühendisisin.
  Kararlarını sınır durum kontrolleriyle gerekçelendir.
  <uzun persona promptu>
prompt_cache: true   # 5 dk cache → sonraki çağrılar %90 daha ucuz
```

## Bekleyen (kapsam DIŞI)
- `cache_creation_input_tokens` vs `cache_read_input_tokens` ayrımı
  ile 013 fiyat hesabı — Görev 015.1
- 1h cache TTL (`type: "1h"`) — YAGNI
- Message-level cache_control — YAGNI

# 009 — Ship

## Sonuç
`Goal.llm_model: str | None = None` opsiyonel alanı eklendi. Anthropic
backend'i öncelik zincirini takip eder:

1. `goal.llm_model` (YAML — görev başına)
2. `ATLAS_LLM_MODEL` env
3. `_DEFAULT_ANTHROPIC_MODEL` sabiti

Claude/ACP backend'ler alanı **yok sayar** (bugünlük — protokolleri
model bildirimi için ayrı yollar kullanır).

003.2'nin `llm_prompt` kalıbıyla simetrik: boş string → None (sessiz
fallback); tip yanlış → `SpecError("llm_model string olmalı, gelen: ...")`.

## Dosyalar
```
src/atlas_core/orchestrator/goals.py      (edit: +llm_model alanı + load kolu)
src/atlas_core/orchestrator/planner.py    (edit: _resolve_anthropic_env(goal) —
                                            goal öncelik + _anthropic_planner geçirir)
tests/test_goals.py                       (+5 test — alan yok/geçerli/boş/null/tip)
tests/test_planner_anthropic.py           (+3 test — goal env üstüne, goal yok →
                                            env, ikisi yok → varsayılan)
pipeline/tasks/009-llm-model/*.md         (5 artefakt)
```

## Sözleşme değişmezliği
- `Goal` yeni alan son sırada + default'lu (003.2 kalıbı).
- `Planner`, `make_planner`, `_call_anthropic` imzaları korundu.
- Mevcut YAML'lar hiç değişmeden çalışır.

## Kalite kapıları
- pytest: **395 passed** (387 → +8)
- mypy strict + ruff: temiz

## Branch
`feat/009-llm-model` — `feat/008-retry-backoff` üstünde tek commit.

## Kullanım örneği
```yaml
goal: "karmaşık analiz"
plan_kind: llm
action_allowlist: [write]
judge_kind: file_exists
judge_arg: rapor.md
budget: 100.0
max_steps: 8
llm_model: claude-3-opus-latest   # bu görev için opus
llm_prompt: |
  Sen kıdemli yapı mühendisisin.
```

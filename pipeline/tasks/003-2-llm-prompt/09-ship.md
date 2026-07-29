# 003.2 — Ship

## Sonuç
`Goal.llm_prompt: str | None = None` opsiyonel alanı YAML'a taşındı;
LLM backend'ler (claude/anthropic/acp) prompt gövdesinin başına
kullanıcı promptunu ekleyip ATLAS'ın plan sözleşmesini altta koruyor.

- **Alan yoksa / None / "":** `goal.llm_prompt is None` → mevcut sabit
  şablon (bit-uyumlu).
- **Alan geçerli str:** başa eklenir; "Görev: ...", context (SPEC 006),
  fiil sözleşmesi + "TEK SATIRLIK" direktifi altta sıralanır. Böylece
  kullanıcı prompt'u sistemin çıktı sözleşmesini bozmaz.
- Değişiklik `_format_prompt`'ta merkezî — üç backend otomatik uyumlu.

## Dosyalar
```
src/atlas_core/orchestrator/goals.py      (edit: +llm_prompt alanı + load kolu)
src/atlas_core/orchestrator/planner.py    (edit: _format_prompt iki-yol dallanma)
tests/test_goals.py                       (+6 test — AC1..AC5)
tests/test_planner_llm.py                 (+1 test — AC8 claude)
tests/test_planner_anthropic.py           (+1 test — AC9 anthropic)
tests/test_planner_acp.py                 (+1 test — AC10 acp)
tests/goals/llm_custom_prompt.yaml        (yeni fixture)
pipeline/tasks/003-2-llm-prompt/*.md      (5 artefakt)
```

## Sözleşme değişmezliği
- `Goal` alan sırasında **eklendi** (son sırada, default'lu) — eski
  positional `Goal(...)` çağrıları etkilenmez (dataclass slots+frozen
  ile yeni alan sonda).
- `_format_prompt(goal, history, context=None)` imzası **korundu**.
- `LLMPlannerError`, `make_planner`, `Planner`, `run_loop` — hiç birinde
  değişiklik yok.

## Kalite kapıları
- pytest hedefli (goals + tüm planner): **85/85 passed**
- pytest genel: **364 passed** (flaky bu turda geçti)
- coverage: %90 eşiğinin üstünde
- mypy strict: temiz; ruff: temiz

## Branch
`feat/003.2-llm-prompt` — `feat/003.1-llm-backends` üstünde tek commit.

## Kullanım örneği
```yaml
# tests/goals/llm_custom_prompt.yaml
goal: "Türkiye lokasyonuna uygun kayıt yaz"
plan_kind: llm
action_allowlist: [write]
judge_kind: file_exists
judge_arg: "kayit.txt"
budget: 20.0
max_steps: 2
llm_prompt: |
  Sen ATLAS'ın kıdemli mühendis planlayıcısısın.
  Kararlarını EN 1993 sınır durum kontrolleriyle gerekçelendir.
  Türkiye lokasyonu, ISO 3833 birimler.
```

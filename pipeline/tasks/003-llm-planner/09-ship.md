# 003 — Ship

## Sonuç
`orchestrator/planner.py` LLM planner (`ATLAS_LLM=claude`) ile canlandı:
- `claude --print --output-format text` subprocess'i her tur planı LLM'den alır.
- Windows uyumlu: `shell=False`, `text=True`, `encoding="utf-8"`,
  `errors="replace"`, `timeout` env-ayarlı (varsayılan 60 sn), stdin ile prompt.
- Fabrika **fail-fast**: bin yok → `LLMPlannerError` anında (run_loop'a girmez).
- CLI yeni exit kodu **7** + audit `llm_error` kaydı — kullanıcı asıl nedeni görür.
- `ATLAS_LLM=stub` (varsayılan) bit-uyumlu; `acp`/`anthropic`/bilinmeyen →
  `NotImplementedError("Görev 003.1'de eklenecek")`.

Bonus (aynı commit): `tests/test_cli_goal.py` + `tests/test_cli_workflow.py`
`_run` helper'larına DECISIONS 2026-07-24 kalıbıyla UTF-8 encoding sabitlendi
— Windows cp1254 locale'da 5 test flaky idi.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py   (edit: 57→170 sat; +LLMPlannerError, +claude backend)
src/atlas_core/cli.py                    (edit: +LLMPlannerError import + iki yakalama noktası)
tests/test_planner.py                    (edit: bilinmeyen backend testi güncellendi + acp/anthropic testi eklendi)
tests/test_planner_llm.py                (yeni, 14 test)
tests/test_cli_direct.py                 (edit: +2 test — bin yok + runtime hata)
tests/goals/llm_claude.yaml              (yeni, 1 fixture)
tests/test_cli_goal.py                   (edit: _run UTF-8 sabit)
tests/test_cli_workflow.py               (edit: _run UTF-8 sabit)
pipeline/tasks/003-llm-planner/*.md      (5 artefakt)
```

## Sözleşme değişmezliği
- `orchestrator/core.py::{run_loop, Action, Judge, CallBudget, LoopResult, StepKind}` **korundu**.
- `orchestrator/planner.py::{Planner, make_planner, PlannerExhaustedError}` **korundu**.
- `Goal` alanları dokunulmadı — mevcut YAML'lar aynen çalışır.
- Yeni sınıf: `LLMPlannerError(RuntimeError)` — N818 uyumlu, `cli.py` yakalar.
- Yeni exit kodu: **7** (LLM planner hatası). Mevcut 2/3/4/5/6 korundu.

## Env sözleşmesi
| Değişken | Değer | Anlam |
|---|---|---|
| `ATLAS_LLM` | `stub` (varsayılan) \| `claude` \| `acp` \| `anthropic` | Backend seçimi |
| `ATLAS_LLM_CLAUDE_BIN` | Mutlak yol (ops.) | claude komutunu geçersiz kıl |
| `ATLAS_LLM_TIMEOUT` | Saniye (ops., varsayılan 60) | Subprocess timeout |

## Kalite kapıları
- pytest: **302/302 passed**
- coverage: **%94.84** (eşik %90)
- mypy strict: temiz
- ruff: temiz

## Branch
`feat/003-llm-planner` — tek commit, `feat/005-gbrain-fts` üstünde.

## Bekleyen (kapsam DIŞI)
- `acp` ve `anthropic` backend'leri — Görev 003.1
- Prompt YAML'da (`Goal.llm_prompt` opsiyonel alanı) — Görev 003.2
- Retry/backoff — Görev 013
- Token cost tracking — Görev 011

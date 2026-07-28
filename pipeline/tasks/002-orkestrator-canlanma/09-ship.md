# 002 — Ship

## Sonuç
`atlas run --goal-file <yaml>` gerçek görevi uçtan uca sürüyor:
- Plan (static / llm stub) → Action (sandbox jailed read/write/shell) →
  Judge (file_exists / regex / exit_zero) → Audit (hash zinciri).
- 8/8 kabul kriteri geçildi, coverage %90, 250 test yeşil.

## Değişen / Eklenen Dosyalar
```
src/atlas_core/cli.py                        (edit)
src/atlas_core/orchestrator/goals.py         (yeni)
src/atlas_core/orchestrator/actions.py       (yeni)
src/atlas_core/orchestrator/planner.py       (yeni)
src/atlas_core/orchestrator/judges.py        (yeni)
tests/test_goals.py                          (yeni, 12)
tests/test_actions.py                        (yeni, 10)
tests/test_planner.py                        (yeni, 4)
tests/test_judges.py                         (yeni, 7)
tests/test_cli_goal.py                       (yeni, 10)
tests/goals/*.yaml                           (6 fikstür)
pipeline/tasks/002-orkestrator-canlanma/     (4 markdown artefakt)
```

## Sözleşme Değişmezliği
- `src/atlas_core/orchestrator/core.py` **dokunulmadı** — `run_loop`,
  `Action`, `Judge`, `CallBudget`, `LoopResult` sözleşmesi korundu.
- Mevcut `atlas run "hedef"` echo demo davranışı korundu (regresyon).

## Kapsam DIŞI (bu görev DEĞİL — sonraki görevler için not)
- **Görev 003:** LLM planner gerçek entegrasyon (`claude` subprocess).
- **Görev 004:** `WorkflowEngine` için `pipeline.*` ve `memory.archive`
  handler'ları — `gorev-tam-tur.yaml` uçtan uca çalışsın.
- **Görev 005:** GBrain SQLite-FTS indeksi (recall O(N·M) → O(log N)).

## Branch & Commit
- Branch: `feat/002-orkestrator-canlanma`
- Commit'ler: 4 (3.1 / 3.2 / 3.3+3.4 / 3.5+3.6 ship)
- PR öncesi: `uv run pytest -q --cov` %90 doğrulandı; mypy strict + ruff temiz.

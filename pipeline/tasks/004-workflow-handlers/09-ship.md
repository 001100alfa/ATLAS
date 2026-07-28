# 004 — Ship

## Sonuç
`atlas workflow run <yaml>` gerçek handler'larla çalışıyor. 3 kanıt
handler (pipeline.gate, pipeline.test, memory.archive) uçtan uca
yürüyor; audit zinciri her adımı yazıyor. Handler başarısızlığı
workflow'u güvenle durduruyor (exit 6). Yıkıcı arşivleme varsayılan
olarak dry-run.

## Dosyalar
```
src/atlas_core/workflows/handlers/
  __init__.py         (register_builtins)
  _errors.py          (HandlerError)
  gate.py
  test.py
  archive.py
src/atlas_core/cli.py                        (edit: workflow subcommand)
tests/workflows/mini.yaml                    (fikstür)
tests/test_handlers.py                       (12)
tests/test_cli_workflow.py                   (6 subprocess e2e)
tests/test_cli_direct.py                     (17 in-process cli)
pipeline/tasks/004-workflow-handlers/*.md    (4 artefakt)
```

## Sözleşme Değişmezliği
- `WorkflowEngine.register/run/StepResult/WorkflowError` **dokunulmadı**.
- `atlas run` (Görev 002) davranışı dokunulmadı.
- `run_loop` sözleşmesi dokunulmadı.

## Kapsam DIŞI (sonraki görevler)
- **003:** LLM planner gerçek entegrasyonu.
- **005:** Kalan pipeline handler'ları (needs/prompts/spec/plan/revise/
  simplify/ship) — LLM veya operatör etkileşimi ister.
- **006:** `requires_approval: true` interaktif akışı.
- **007:** GBrain SQLite-FTS indeksi.

## Branch & Commit
Branch: `feat/004-workflow-handlers` — tek commit'te ship (küçük görev).

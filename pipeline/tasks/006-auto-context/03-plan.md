# 006 — PLAN

## WBS
| # | Adım | Çıktı | Gate |
|---|---|---|---|
| 3.1 | Branch aç: feat/006-auto-context | git | branch checkout |
| 3.2 | `goals.py`: `Goal.inject_context: bool=True` + `context_limit: int=5` opsiyonel alanları; `load_goal` doğrulaması | src/atlas_core/orchestrator/goals.py, tests/test_goals.py'a 3 test | pytest yeşil |
| 3.3 | `planner.py`: `make_planner(goal, context=None)` — LLM claude closure prompt'a bağlam ekler; static/stub context'i yok sayar; `_format_prompt` `context: str \| None` alır | planner.py edit, test_planner_llm.py'a 2-3 test | AC1, AC4 yeşil |
| 3.4 | `cli.py::_cmd_run_goal`: `_context_enabled(goal)` yardımcısı + GBrain çağrısı + `make_planner(goal, ctx)` + stderr uyarı + stdout "Bağlam:" başlığı | cli.py edit, test_cli_direct.py'a 3-4 test | AC5-AC7, AC9 yeşil |
| 3.5 | Kalite: ruff + mypy strict + coverage ≥ %90 | full gate | tümü yeşil |
| 3.6 | 06-test-report + 09-ship + DECISIONS 2026-07-29 (006 girdisi) + commit | pipeline artefaktlar + git commit | manuel doğrulama |

## Risk
| # | Risk | Azaltma |
|---|---|---|
| R1 | GBrain FTS index oluşturma disk yazımı gerektirir; test tmp_path'te izole | conftest / _env helper zaten tmp vault kullanıyor; `.atlas/gbrain.sqlite` oraya yazılır |
| R2 | Sözleşme genişletme (`make_planner` yeni kwarg) mevcut çağıranları kırar mı | Default `None` — mevcut çağrılar aynen çalışır; test_planner.py + test_planner_llm.py yeşil kalır |
| R3 | GBrain hatası görevi kırar | try/except + stderr uyarı; FR6 test edilir |
| R4 | `Goal` alan eklemesi mypy strict dataclass kalıbıyla uyumsuz | field(default=True) + Literal daraltması testte kanıtlanır |
| R5 | LLM prompt uzar, subprocess arg limit veya token bütçesini aşar | context_limit üst sınırı 50; `_MAX_CONTEXT_CHARS = 4000` iç kısaltma emniyeti (FR6 dışı ama koruma) |

## Rollback
Tek atomik commit. Gate düşerse `git reset --hard HEAD~1`. Default davranış
`inject_context=True` + `ATLAS_CONTEXT=on` — kullanıcı istemezse
`ATLAS_CONTEXT=off` ile eski davranışa döner (kod değişimi gerektirmez).

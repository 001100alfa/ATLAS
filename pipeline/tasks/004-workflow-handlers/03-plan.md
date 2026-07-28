# 004 — PLAN

## WBS
| # | Adım | Çıktı | Gate |
|---|---|---|---|
| 3.1 | `handlers/` paketi + `gate` + `HandlerError` + test | `handlers/{__init__,gate}.py`, `test_handlers_gate.py` | pytest yeşil + mypy strict + ruff |
| 3.2 | `test` handler + subprocess sarmalayıcı + test | `handlers/test.py`, `test_handlers_test.py` | pytest yeşil (dry-run + gerçek küçük koşu) |
| 3.3 | `archive` handler + test | `handlers/archive.py`, `test_handlers_archive.py` | pytest yeşil (dry-run tam, gerçek arşiv tmp_path'te) |
| 3.4 | `register_builtins` + CLI `workflow run` + fikstür + e2e test | `handlers/__init__.py`, `cli.py` edit, `tests/workflows/mini.yaml`, `test_cli_workflow.py` | AC1–AC7 yeşil |
| 3.5 | Öz-denetim | ruff + mypy `src` + coverage ≥ %90 | CI yeşil |
| 3.6 | Ship | test-report + ship + DECISIONS + commit | manuel doğrulama |

## Risk
| # | Risk | Azaltma |
|---|---|---|
| R1 | pytest subprocess kendini rekürsif çağırır (test-in-test) | e2e testte `paths=["tests/goals"]` gibi minik alt-küme; ana suite çağrılmaz |
| R2 | archive_task shutil.rmtree — canlı klasörü siler | Handler varsayılanı `dry_run=True`; gerçek testte tmp_path'e kopyalanmış görev kullanılır |
| R3 | Windows subprocess UTF-8 | `encoding="utf-8", errors="replace"` sabit |
| R4 | WorkflowEngine sözleşme kırılırsa mevcut engine testleri patlar | engine.py'a dokunulmaz; yalnız yeni handler modülleri eklenir |

## Rollback
Her adım atomik commit; gate düşerse `git reset --hard HEAD~1` (onay ile).

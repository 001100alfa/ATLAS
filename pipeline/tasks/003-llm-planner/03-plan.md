# 003 — PLAN

## WBS
| # | Adım | Çıktı | Gate |
|---|---|---|---|
| 3.1 | Branch aç, planner.py'ye `LLMPlannerError`, `_resolve_claude_bin`, `_format_prompt`, `_call_claude`, `_claude_planner` ekle; `make_planner` dallanmasını genişlet | src/atlas_core/orchestrator/planner.py | ruff + mypy strict yeşil |
| 3.2 | Birim testler: `tests/test_planner_llm.py` (AC1..AC9 + AC11) — subprocess monkeypatch kalıbıyla | tests/test_planner_llm.py | pytest -q yeşil |
| 3.3 | CLI `_cmd_run_goal` içine `LLMPlannerError` yakalama + exit 7 + audit "llm_error" kaydı; test_cli_direct'e AC10 testi | src/atlas_core/cli.py, tests/test_cli_direct.py | in-process test yeşil |
| 3.4 | Örnek YAML: `tests/goals/llm_claude.yaml` (plan_kind=llm) — test için | tests/goals/llm_claude.yaml | test AC10 tüketir |
| 3.5 | Kalite kapıları: ruff + mypy strict + coverage ≥ %90 | full gate yeşil | tümü yeşil |
| 3.6 | 06-test-report + 09-ship + DECISIONS 2026-07-29 girdisi + commit | pipeline artefaktlar + git commit | manuel doğrulama |

## Risk
| # | Risk | Azaltma |
|---|---|---|
| R1 | Windows'ta `.cmd` shim'i `shell=False`'da açılmaz | `shutil.which("claude")` tam yol döner (.cmd dahil); Python 3.12 subprocess bu uzantıyı destekler. Testte gerçek subprocess YOK — monkeypatch. Gerçek çağrı FR3'e uyar; belgeye eklenir. |
| R2 | Prompt Türkçe karakter → subprocess encoding çakışması | `text=True, encoding="utf-8", errors="replace"`; input stdin'den (arg-quote yok). |
| R3 | LLM cevabı non-plan (açıklama, kod bloğu) | İlk satırı al; boşluk temizle; boşsa hata. Sözleşme: LLM tek satır dönmezse tur biter — kullanıcı promptu tune eder (ileri görev). |
| R4 | `test_planner.py::test_llm_bilinmeyen_backend` bozulur (claude artık NotImplementedError değil) | Test güncellenir: "xyz" gibi bilinmeyen backend'e taşınır — semantik korunur. |
| R5 | subprocess.run monkeypatch farklı sürümlerde farklı imza | Testte `monkeypatch.setattr("atlas_core.orchestrator.planner.subprocess.run", fake)` — modüle özgü, kararlı. |
| R6 | mypy strict `subprocess.run` overload çözemez | Argümanları named + `capture_output=True` overloadu tetikler; dönüş `CompletedProcess[str]`. Cast gerekirse dar. |

## Rollback
Adım commit'leri atomik değil (tek commit sonda). Gate düşerse
`git reset --hard <baseline>` (feat/005-gbrain-fts HEAD). Fallback
tasarımı: `ATLAS_LLM=stub` bit-uyumlu — hata durumunda kullanıcı env
değişkeniyle eski davranışa döner.

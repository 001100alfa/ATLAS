# 002 — Test Raporu

## Kapsam
- **Toplam pytest:** 250 test / 250 yeşil
- **Yeni testler (bu görev):** 43
  - `test_goals.py` — 12
  - `test_actions.py` — 10
  - `test_planner.py` — 4
  - `test_judges.py` — 7
  - `test_cli_goal.py` — 10
- **Regresyon dokunulmadı:** `test_platform.py`, `test_core.py`,
  `test_cli.py`, `test_portable.py`, `test_doctor_*`, `test_juggler_*`,
  `test_make_portable.py`, `test_setup_gui.py` — hepsi yeşil.

## Kabul Kriterleri (SPEC §3)
| # | Kriter | Test | Durum |
|---|---|---|---|
| AC1 | hello.yaml → done=True, exit 0, audit ≥ 5 kayıt, verify OK | `test_run_goal_file_hello`, `test_run_audit_verify_gecerli` | ✅ |
| AC2 | İzin ihlali (fiil) → exit 5, denied, dosya yok | `test_run_deny_senaryolari[denied_verb]` | ✅ |
| AC3 | Allowlist dışı shell → exit 5, denied | `test_run_deny_senaryolari[denied_shell]` | ✅ |
| AC4 | Path kaçışı → exit 5, sandbox dışına yazılmamış | `test_run_deny_senaryolari[escape]` | ✅ |
| AC5 | Bütçe → exit 3 | `test_run_butce_asimi` | ✅ |
| AC6 | LLM stub → deterministik, döngü sonu | `test_run_llm_stub_max_steps` | ✅ |
| AC7 | Regresyon: `atlas run "eski hedef"` echo demo çalışır | `test_run_eski_pozitif_regresyon` + `test_platform.py` | ✅ |
| AC8 | audit-verify exit 0 | `test_run_audit_verify_gecerli` | ✅ |

## NFR
- **NF1 mypy strict:** 19 src dosyası temiz ✅
- **NF2 ruff:** src+tests temiz ✅
- **NF3 coverage:** toplam %90 (gate ≥ %90) ✅
- **NF4 Windows:** tüm testler `win32` python 3.12.6'da yeşil ✅
- **NF5 determinism:** `--run-id` bayrağı ile sandbox path'i sabitlenir ✅

## Ölçülebilir Başarı (00-need.md)
- **M1:** hello.yaml done=True, exit 0 ✅
- **M2:** audit-verify exit 0 ✅
- **M3:** koşuda ≥ 5 audit kaydı (test assert) ✅
- **M4:** sandbox kaçış reddi + audit "denied" ✅
- **M5:** yeni testler yeşil, coverage %90 korundu, regresyon temiz ✅

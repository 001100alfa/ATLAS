# 003 — Test Raporu

## Kalite kapıları
- **pytest**: 302 passed, 0 failed (mono-worker, 45 sn)
- **coverage**: %94.84 (eşik %90 ✔). `planner.py` %97, `cli.py` etkilenen dallar %85+
- **mypy strict**: 25 dosya temiz
- **ruff**: All checks passed

## AC → test eşleştirmesi

| AC | Test | Sonuç |
|---|---|---|
| AC1 stub bit-uyumlu | `tests/test_planner.py::test_llm_stub_deterministik` | ✔ |
| AC2 fabrika bin bulunur | `test_planner_llm.py::test_fabrika_bin_env_ile_bulunur`, `test_fabrika_bin_shutil_which_ile_bulunur` | ✔ |
| AC3 bin yok fabrika hata | `test_planner_llm.py::test_bin_yok_fabrika_hata`, `test_bin_env_yanlis_yol` | ✔ |
| AC4 happy call | `test_planner_llm.py::test_call_happy` | ✔ |
| AC5 timeout | `test_planner_llm.py::test_call_timeout` (2 çağrı ile kalıcı bozulmama teyidi) | ✔ |
| AC6 non-zero exit | `test_planner_llm.py::test_call_non_zero_exit`, `test_call_non_zero_exit_bos_stderr` | ✔ |
| AC7 boş cevap | `test_planner_llm.py::test_call_bos_cevap` | ✔ |
| AC8 çok satırlı → ilk | `test_planner_llm.py::test_call_cok_satirli_ilk_satir` | ✔ |
| AC9 UTF-8 (Türkçe+emoji) | `test_planner_llm.py::test_call_utf8_turkce_ve_emoji` | ✔ |
| AC10 CLI exit 7 + audit | `test_cli_direct.py::test_run_llm_claude_bin_yok`, `test_run_llm_claude_runtime_hatasi` | ✔ |
| AC11 bilinmeyen backend | `test_planner.py::test_llm_bilinmeyen_backend`, `test_llm_acp_ve_anthropic_erteleme`, `test_planner_llm.py::test_backend_bilinmiyor` | ✔ |
| AC12 kalite kapıları | ruff+mypy+coverage yukarıda | ✔ |

Ek testler (SPEC dışı ama değerli):
- `test_prompt_history_gozlemleri_alir`: prompt'a son 3 OBSERVE gerçekten geçiyor mu (regresyon zırhı).
- `test_call_oserror`: subprocess başlatılamazsa `LLMPlannerError("başlatılamadı")`.

## Regresyon
- `test_platform.py::test_gbrain_recall_*`, `test_core.py`, `test_actions.py`,
  `test_judges.py`, `test_goals.py`, `test_workflow_*` — yeşil.
- `test_cli_goal.py` + `test_cli_workflow.py` — 5 testin Windows cp1254 flaky'liği
  `_run` helper'larına `encoding="utf-8", errors="replace"` eklenerek kapatıldı.
  Kalıp DECISIONS 2026-07-24 (üstsimge birimleri) — CLI çıktısını **okuyan**
  taraf için de aynı sabitleme şart.

## Bilinen flaky
- `test_doctor_gui.py::test_restore_defaults_to_newest_and_can_pick_by_name`
  ilk turda Windows mtime granülerliğine takılabiliyor (arka arkaya 2 test aynı
  saniyede yedek oluşturuyor). İzole çalıştırmada ve tekrarda geçer. 003 dışı;
  Görev 007+ için not.

## Elle doğrulama (opsiyonel)
`ATLAS_LLM=claude atlas run --goal-file tests/goals/llm_claude.yaml`
komutu bin PATH'te varsa gerçek subprocess çağrısını üretir. Test suite mock ile
gezdiği için CI'da harici bağımlılık yok — deterministik.

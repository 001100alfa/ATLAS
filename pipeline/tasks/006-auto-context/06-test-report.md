# 006 — Test Raporu

## Kalite kapıları
- **pytest**: 319 passed (17 yeni: 5 goals + 6 planner_llm + 6 cli_direct)
- **coverage**: %94.85 (eşik %90 ✔). `goals.py` %86, `cli.py` %85+ etkilenen dallar
- **mypy strict**: 25 dosya temiz
- **ruff**: All checks passed

## AC → test eşleştirmesi

| AC | Test | Sonuç |
|---|---|---|
| AC1 LLM+context prompt'ta | `test_planner_llm.py::test_006_context_prompt_a_eklenir` | ✔ |
| AC2 boş context bloğu eklenmez | `test_planner_llm.py::test_006_bos_context_bloguyok`, `test_006_none_context_prompt_blogu_eklemez` | ✔ |
| AC3 static regresyon | `test_planner_llm.py::test_006_static_backend_context_yok_sayar`, `test_cli_direct.py::test_006_static_gorevde_baglam_kapali` | ✔ |
| AC4 stub context yok sayar | `test_planner_llm.py::test_006_stub_backend_context_yok_sayar` | ✔ |
| AC5 `ATLAS_CONTEXT=off` env | `test_cli_direct.py::test_006_atlas_context_off_env` | ✔ |
| AC6 `Goal.inject_context: false` | `test_cli_direct.py::test_006_goal_inject_context_false` | ✔ |
| AC7 GBrain hata izolasyonu | `test_cli_direct.py::test_006_gbrain_hata_izole` | ✔ |
| AC8 Goal doğrulama | `test_goals.py::test_006_inject_context_bool_degilse`, `test_006_context_limit_negatif`, `test_006_context_limit_ust_sinir`, `test_006_context_limit_bool_reddedilir`, `test_006_default_inject_context_ve_limit` | ✔ (5) |
| AC9 CLI görünürlük | `test_cli_direct.py::test_006_llm_gorevde_baglam_hesaplanir`, `test_006_baglam_var_ise_sayilir`, `test_006_atlas_context_off_env` | ✔ |
| AC10 kalite | ruff+mypy+coverage yukarıda | ✔ |

Ek test:
- `test_006_uzun_context_kirpilir`: `_MAX_CONTEXT_CHARS = 4000` emniyeti
  (SPEC dışı ama prompt şişme koruması).

## Regresyon
- 302 önceki testin hepsi yeşil (17 yeni ekleme + 0 kırma).
- Yeni `Goal` alanları default'lu — mevcut `tests/goals/*.yaml` fixture'ları
  hiç değişmeden yükleniyor.
- `make_planner` yeni kwarg pozisyonel değil (opsiyonel) — 003 testleri yeşil.
- `test_platform.py::test_gbrain_recall_*` yeşil (GBrain sözleşmesi korundu).

## Bilinen flaky
- `test_doctor_gui.py::test_restore_defaults_to_newest_and_can_pick_by_name`
  ilk turda düşebilir, ikinci turda geçer (Windows mtime granülerliği).
  DEVAM_NOKTASI'nda 003'ten kalan not; 006 dışı.

## Manuel doğrulama örneği (opsiyonel)
```
atlas remember dosya-yaz "dosya yazma notları için ayrıntılar"
ATLAS_LLM=stub atlas run --goal-file tests/goals/llm_stub.yaml --run-id manuel
# stdout: "Bağlam: 1 not enjekte edildi" (veya "Bağlam: yok" — vault'a bağlı)
```

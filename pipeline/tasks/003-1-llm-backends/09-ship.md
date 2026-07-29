# 003.1 — Ship

## Sonuç
`orchestrator/planner.py` iki yeni LLM backend'i kazandı:

- **`ATLAS_LLM=anthropic`** — Anthropic Messages API'sine stdlib `urllib`
  ile doğrudan HTTPS POST. `ANTHROPIC_API_KEY` zorunlu; `ATLAS_LLM_MODEL`
  (varsayılan `claude-3-5-sonnet-latest`) ve `ATLAS_LLM_ANTHROPIC_URL`
  opsiyonel override. Yerel `claude` CLI kurulumu **şart değil**.
- **`ATLAS_LLM=acp`** — `ATLAS_LLM_ACP_BIN` ile başlatılan subprocess'a
  Agent Client Protocol alt-kümesi (initialize → session/new →
  session/prompt → `agent_message_chunk` bloklarını topla) üzerinden
  text prompt. Görev başına tek-oturum; kalıcı bağlantı yok; süreç
  sızıntısı yasağı `finally` + kill ile garantili.

Görev 006 context injection (`context=` kwarg) her iki backend'e
otomatik geçti — `_format_prompt` yardımcısı ortak.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py   (edit: 199 → ~430 sat;
                                          +_anthropic_planner, +_acp_planner,
                                          +iç yardımcılar; make_planner dallanma)
tests/test_planner_anthropic.py          (yeni, 18 test)
tests/test_planner_acp.py                (yeni, 17 test)
tests/test_planner.py                    (edit: bilinmeyen backend mesajı
                                          güncellendi; erteleme testi kaldırıldı)
tests/test_cli_direct.py                 (edit: +2 test — anthropic key yok,
                                          acp bin yok, ikisi de exit 7 + audit)
tests/goals/llm_anthropic.yaml           (yeni, 1 fixture)
pipeline/tasks/003-1-llm-backends/*.md   (5 artefakt)
```

## Sözleşme değişmezliği
- `orchestrator/core.py::{run_loop, Action, Judge, CallBudget,
  LoopResult, StepKind}` **korundu**.
- `orchestrator/planner.py::{Planner, make_planner, PlannerExhaustedError,
  LLMPlannerError}` **imzaları korundu** — yeni yalnız iç yardımcı.
- `Goal` alanları dokunulmadı — YAML'lar aynen çalışır.
- Exit kodu **7** genişledi (yeni sebep): `LLMPlannerError` her iki
  backend'de de aynı istisnayı fırlatır, CLI koduna dokunma gerekmedi.

## Env sözleşmesi (kümülatif)
| Değişken | Değer | Anlam |
|---|---|---|
| `ATLAS_LLM` | `stub`\|`claude`\|`anthropic`\|`acp` | Backend seçimi |
| `ATLAS_LLM_TIMEOUT` | saniye (varsayılan 60) | Ortak timeout |
| `ATLAS_LLM_CLAUDE_BIN` | mutlak yol | 003: claude subprocess override |
| `ANTHROPIC_API_KEY` | sk-... | **anthropic zorunlu** |
| `ATLAS_LLM_MODEL` | model id | **anthropic** — varsayılan `claude-3-5-sonnet-latest` |
| `ATLAS_LLM_ANTHROPIC_URL` | URL | **anthropic** — vekil/test override |
| `ATLAS_LLM_ACP_BIN` | mutlak yol | **acp zorunlu** (veya PATH'te `acp-agent`) |
| `ATLAS_LLM_ACP_ARGS` | argv | **acp** — boşluklu ek argümanlar (shlex) |

## Kalite kapıları
- pytest hedefli (planner + CLI + regresyon): **91/91 passed**
- pytest genel: **354 passed + 1 bilinen flaky** (doctor_gui,
  Görev 007 son adımı düzeltiyor)
- coverage genel: **%93.52** (eşik %90); planner.py %89 (yeni ACP
  hata kolları — kalan branch'ler in-vivo testte çıkacak)
- mypy strict: temiz (25 src dosyası)
- ruff: temiz (src + tests)
- `atlas scan src`: sır bulunamadı

## Branch
`feat/003.1-llm-backends` — main üstünde tek commit hazırlanacak.

## Bekleyen (kapsam DIŞI)
- Prompt YAML'da (`Goal.llm_prompt` opsiyonel alanı) — **Görev 003.2** (sıradaki)
- Retry/backoff — Görev 013
- Token cost tracking — Görev 011
- ACP tool-use, streaming, permissions — Görev 010+

## Notlar
- API key hiçbir kod yolunda stderr / audit / log'a yazılmaz —
  `test_key_asla_hata_mesajina_gecmez` bunu doğruluyor (defense-in-depth).
- ACP alt kümesi: `available_commands_update`, `plan` gibi bilinmeyen
  notification'lar sessizce yok sayılır (forward-compatible).
- Windows subprocess pipe deadlock riski `bufsize=1` + monotonic
  timeout + `readline` + `finally kill` ile ele alındı; test tarafında
  Popen monkeypatch belirlenimci.

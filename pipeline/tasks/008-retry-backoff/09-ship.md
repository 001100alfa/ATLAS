# 008 — Ship

## Sonuç
LLM planner çıktısına opsiyonel retry sarmalayıcı: `make_retrying_planner(
inner, retries, backoff_s)`. Env kapalıysa (varsayılan) sarma no-op.
Env açıksa `LLMPlannerError` yakalanır, üstel backoff (`backoff * 2**attempt`)
sonrası N-1 kez yeniden denenir; son deneme raise.

- **`ATLAS_LLM_RETRIES`** (varsayılan 0 = kapalı)
- **`ATLAS_LLM_BACKOFF`** (varsayılan 1.0 sn)
- **`ATLAS_LLM_TRACE=1`** → her başarısız deneme stderr'da
  `[retry] deneme N/M başarısız: <mesaj>` satırı

Üç backend'e (claude/anthropic/acp) aynı sözleşmeyle uygulanır —
sarmalayıcı planner'ın **dışında** durur.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +_sleep hook, +_read_retry_env,
                                            +make_retrying_planner)
src/atlas_core/cli.py                     (edit: _cmd_run_goal inner→plan zinciri)
tests/test_planner_retry.py               (yeni, 15 test)
tests/test_cli_direct.py                  (+1 test — retries=2 env, 3 çağrı, exit 7)
pipeline/tasks/008-retry-backoff/*.md     (5 artefakt)
```

## Sözleşme değişmezliği
- `Planner`, `make_planner`, `PlannerExhaustedError`, `LLMPlannerError`
  imzaları **korundu**.
- Sarmalayıcı `Callable[[str, list], str]` döner — `run_loop` fark etmez.
- Yalnız `LLMPlannerError` yakalanır; `PlannerExhaustedError`,
  `KeyboardInterrupt`, `ValueError` vb. **sarma geçer**.

## Kalite kapıları
- pytest: **387 passed** (371 → +16)
- coverage: %90 üstünde
- mypy strict + ruff: temiz

## Branch
`feat/008-retry-backoff` — main üstünde tek commit.

## Bekleyen (kapsam DIŞI)
- Jitter (rastgele salınım) — Görev 013
- HTTP `Retry-After` header'ı — Görev 011 + 013
- Retry içinde farklı backend'e geçiş — protokol dışı

# 014 — Ship

## Sonuç
Retry sarmalayıcısı iki iyileştirme kazandı:

- **Jitter:** `ATLAS_LLM_JITTER=0.5` env'inde `[0, 0.5)` rastgele
  salınım backoff üstüne eklenir. Thundering herd önlenir.
  Jitter 0 (varsayılan) → 008 davranışı bit-uyumlu.
- **Retry-After header:** `_call_anthropic` `HTTPError` yakaladığında
  response'ta `Retry-After` başlığı varsa `RetryAfterError`
  (`LLMPlannerError` alt sınıfı) fırlatır; sarmalayıcı bu istisnayı
  yakalarsa **backoff yerine header saniyesi** kullanır — sunucu
  ipucuna saygı. Jitter header verildiğinde eklenmez.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +RetryAfterError,
                                            +_read_jitter_env,
                                            +_parse_retry_after,
                                            _call_anthropic HTTPError kolu,
                                            make_retrying_planner jitter+header)
tests/test_planner_retry.py               (+7 test — jitter env/deterministik,
                                            RetryAfter header saniyesi,
                                            karışık akış)
tests/test_planner_anthropic.py           (+4 test — 429/529 with header,
                                            without header, parse hatası)
pipeline/tasks/014-retry-jitter-header/*.md (5 artefakt)
```

## Sözleşme değişmezliği
- `Planner`, `make_planner`, `make_retrying_planner`, `LLMPlannerError`
  imzaları korundu.
- `RetryAfterError` **yeni** — `LLMPlannerError` alt sınıfı; mevcut
  `except LLMPlannerError` yakalamaları hâlâ çalışır (LSP uyumlu).
- Jitter 0 → 008 davranışı bit-uyumlu (mevcut testler yeşil).
- claude/acp backend'ler `RetryAfterError` fırlatmaz (native header
  yok); jitter üç backend'de de çalışır (sarmalayıcı seviyesi).

## Kalite kapıları
- pytest: **430 passed** (420 → +10)
- mypy strict + ruff: temiz

## Branch
`feat/014-retry-jitter-header` — 010.1 üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM_JITTER` | Üst-sınır saniye (varsayılan 0.0 = kapalı) |

## Bekleyen
- HTTP-Date formatı `Retry-After` (RFC 7231) — Anthropic saniye
  kullanır, kapsam DIŞI.
- Global retry_after cap — `ATLAS_LLM_TIMEOUT` yeter.

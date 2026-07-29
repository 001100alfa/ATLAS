# 016.2 — Ship

## Sonuç
`session/request_permission` request'ine otomatik karar dönüyor:
- Read-only tool (`fs/read_text_file`) → `allow_once`
- Write/shell tool → `reject`
- Bilinmeyen tool → `reject` (savunmalı varsayılan)

Kullanıcı UI dialogu asla görmez — ATLAS otonom karar verir.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: _acp_handle_client_request
                                            session/request_permission dallanma,
                                            +_acp_permission_response ~50 sat)
tests/test_planner_acp.py                 (+4 test — read allow, write reject,
                                            bilinmeyen reject, options yok fallback)
pipeline/tasks/016-2-acp-permission/*.md  (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_acp` sözleşmesi korundu.
- `LLMPlannerError` mevcut; yeni exception YOK.
- 016 + 016.1 davranışları bit-uyumlu (regresyon testleri yeşil).

## Kalite kapıları
- pytest: **490 passed** (486 → +4)
- mypy strict + ruff: temiz

## Branch
`feat/016.2-acp-permission` — main üstünde tek commit.

## Bekleyen
- 016.3: interaktif kullanıcı dialogu (opt-in)
- 016.4: session-level "her zaman izin ver" hafızası

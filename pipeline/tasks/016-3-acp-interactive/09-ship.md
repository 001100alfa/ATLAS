# 016.3 — Ship

## Sonuç
`ATLAS_ACP_INTERACTIVE=1` env'inde ACP permission dialog kullanıcıdan
stdin'den y/n sordurur. Env kapalıysa 016.2 auto-karar bit-uyumlu.

- `y`/`yes`/`allow_once`/`allow` → `allow_once`
- `n`/`no`/`reject` → `reject`
- Boş satır → default (016.2 auto-karar)
- EOF/KeyboardInterrupt/OSError → auto-karar (fail-safe)

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: _acp_permission_response
                                            ATLAS_ACP_INTERACTIVE dallanma;
                                            +_prompt_acp_permission ~20 sat)
tests/test_planner_acp.py                 (+4 test — env kapalı bit-uyumlu,
                                            y kabul, n red, boş default)
pipeline/tasks/016-3-acp-interactive/*.md (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_acp` sözleşmesi korundu.
- Env kapalı → 016.2 bit-uyumlu.
- Fail-safe: kullanıcı yanıtı bozuksa auto-karara düş.

## Kalite kapıları
- pytest: **522 passed** (518 → +4)
- mypy strict + ruff: temiz

## Branch
`feat/016.3-acp-interactive` — main üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_ACP_INTERACTIVE=1` | ACP permission stdin'den sor (varsayılan otomatik) |

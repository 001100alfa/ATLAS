# 019.1 — Ship

## Sonuç
`_call_acp` `agent_message_chunk` chunk'larını biriktirirken **ilk
`\n`'da erken çık**; kalan chunk'lar okunmaz. Anthropic streaming
(019) ile birebir simetri: algılanan gecikme düşer, oturum kısalır.

- İlk satır boşsa (`"\n"` sadece) beklemez, sonraki chunk okunur.
- Süreç `finally _acp_teardown` bloğunda kill (016 bit-uyumlu).
- Tek satır + newline yok → stopReason ile normal biter (mevcut yol).

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: _call_acp
                                            agent_message_chunk ilk newline
                                            break — ~5 sat)
tests/test_planner_acp.py                 (+3 test — iki chunk newline erken,
                                            boş newline devam, tek satır normal)
pipeline/tasks/019-1-acp-streaming/*.md   (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_acp` imzası korundu.
- 016 tool_call red + 016.1 request + 016.2/016.3 permission davranışları
  bit-uyumlu.
- Süreç kill garantisi (finally teardown) korundu.

## Kalite kapıları
- pytest: **533 passed** (530 → +3)
- mypy strict + ruff: temiz

## Branch
`feat/019.1-acp-streaming` — 018.1 üstünde tek commit.

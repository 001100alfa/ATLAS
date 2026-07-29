# 016 — Ship

## Sonuç
ACP backend'i agent'ın `tool_call` / `tool_call_update` bildirimlerini
sessizce yok saymak yerine **açık red** ediyor artık:

```
LLMPlannerError: acp: tool-use şu an desteklenmiyor (Görev 016.1+);
agent tool_name='read_file' istedi
```

Süreç `finally _acp_teardown` bloğunda kapatılır (kill garantisi).
Diğer notification'lar (`agent_message_chunk`, bilinmeyen türler)
mevcut davranışta — sessizce atlanır.

Tam tool-use desteği Görev 016.1+'de; bu görev **açık kapı** olarak
hata yolunu net tanımladı, kullanıcı fake sonuç görmüyor.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: _call_acp session/update
                                            dispatcher — tool_call/update red,
                                            agent_message_chunk topla,
                                            bilinmeyen atla)
tests/test_planner_acp.py                 (+3 test — tool_call red,
                                            tool_call_update red,
                                            bilinmeyen sessionUpdate atlanır)
pipeline/tasks/016-acp-tool-reject/*.md   (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_acp` imzası korundu.
- `LLMPlannerError` mevcut sınıf — yeni exception YOK.
- Süreç yaşam döngüsü (`_acp_teardown` kill) 003.1'den beri sağlam;
  bu görev yalnız hata dallanmasını ekledi.

## Kalite kapıları
- pytest: **440 passed** (437 → +3)
- mypy strict + ruff: temiz

## Branch
`feat/016-acp-tool-reject` — 015 üstünde tek commit.

## Bekleyen
- Görev 016.1: tam tool-use — MCP forwarding + izin dialog'u +
  ACP `session/request_permission` + gerçek tool yürütme.

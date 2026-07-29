# 016 — İhtiyaç: ACP `tool_call` açık red

## Bağlam
SPEC 003.1 ACP alt-kümesi text-only — `session/update` içindeki
`agent_message_chunk` bildirimlerini topluyor, id=3 response'unu
bekliyor, `stopReason`'da kapanıyor. Ancak ACP protokolünde agent
`tool_call_request` gönderebilir: dosya oku, komut çalıştır, izin
iste. ATLAS'ın ACP client'ı bu sinyalleri şu an **sessizce yok
sayıyor** — agent tool çağırmak isterse cevap alamaz, sonsuz
bekleyebilir veya boş plan üretir.

Tam tool-use desteği büyük bir iş (Görev 016.1+); şu an ihtiyaç
**açık red**: agent tool_call gönderirse anlaşılır bir hata mesajı
al, subprocess'i kapa, `LLMPlannerError` fırlat.

## İhtiyaç (tek cümle)
`session/update` `sessionUpdate == "tool_call"` bildirimi geldiğinde
`_call_acp` sessizce yok saymak yerine `LLMPlannerError("acp: tool-use
şu an desteklenmiyor (Görev 016.1+); agent tool_name=<X> istedi")`
fırlatsın; süreç `finally` bloğunda kill'lenir.

## Ölçülebilir Başarı
- **M1 — Tool_call yakala:** `session/update` içinde `sessionUpdate
  == "tool_call"` → içinden `toolCall.name` (veya `title`) çıkar,
  Türkçe mesajlı `LLMPlannerError` fırlat.
- **M2 — Süreç sızıntısı yok:** `finally` bloğu mevcut (`_acp_teardown`);
  hata fırlatılınca süreç kill.
- **M3 — Diğer notification'lar korunur:** `agent_message_chunk`,
  `plan`, `available_commands_update` gibi bilinen/bilinmeyen
  bildirim türleri **sessizce yok sayılır** (bugünkü davranış korundu).
- **M4 — `tool_call_update` da red:** aynı gerekçeyle
  `sessionUpdate == "tool_call_update"` bildirimi de red — bu tool
  sonucu güncellemesidir; agent tool başlattıysa update de gelir.
- **M5 — Test:** +3 test — tool_call red, tool_call_update red,
  bilinmeyen sessionUpdate atlanır (regresyon).
- **M6 — DECISIONS:** [KARAR] neden açık red; tool-use tam sözleşmesi
  Görev 016.1+.

## Kapsam DIŞI
- Gerçek tool yürütme (izin dialog'u, dosya erişim, MCP forwarding).
- `session/request_permission` — permission dialog'ları protokolde
  ayrı; agent tool'a çıkmadan önce izin isteyebilir. Bu görevde
  yok sayılır (fabrikada varsa boş cevap → agent otomatik ret'e düşer).
- claude/anthropic backend'e tool-use — anthropic backend `messages`
  API'sinde tool_use blokları destekler ama bu ATLAS'ın planner
  sözleşmesiyle uyumlu değil; ayrı görev.

## Kısıt
- `_call_acp` mevcut sözleşme (`(bin, extra, prompt, timeout) -> str`)
  korunur.
- `LLMPlannerError` mevcut sınıf; yeni exception YOK.
- Türkçe mesaj; istisna adları `*Error` sonekli.

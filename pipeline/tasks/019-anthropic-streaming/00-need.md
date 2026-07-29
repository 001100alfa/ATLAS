# 019 — İhtiyaç: Anthropic streaming (opt-in)

## Bağlam
Anthropic Messages API request'e `"stream": true` eklenirse response
SSE (Server-Sent Events) formatında akar. ATLAS'ın planner sözleşmesi
**tek satır** dönüyor; streaming tam text tamamlanmasını beklemeden
**ilk newline'ı** yakalayınca planı çıkarabilir → algılanan gecikme
düşer.

## İhtiyaç (tek cümle)
`Goal.stream: bool = False` opsiyonel alanı ile YAML'da streaming
açılabilsin; True ise request'e `stream: true` eklensin, response
SSE olarak parse edilsin, `content_block_delta` `text_delta`
event'lerinden metin biriktir; ilk newline gelince kes ve bağlantıyı
kapa.

## Ölçülebilir Başarı
- **M1 — Alan opsiyonel:** `Goal.stream: bool = False`; eski YAML'lar
  hiç değişmeden yüklenir; tip yanlış → `SpecError`.
- **M2 — Non-streaming korunur:** `stream=False` (varsayılan) →
  mevcut `_call_anthropic` davranışı **bit-uyumlu** (011/015.1 yolu).
- **M3 — Streaming payload:** `stream=True` → request body'ye
  `"stream": true` eklenir; response `Content-Type: text/event-stream`.
- **M4 — SSE parse:** SSE format: her event `data: {json}\n\n` bloğu;
  bizim ilgilendiğimiz `event: content_block_delta` +
  `data: {"type":"content_block_delta","delta":{"type":"text_delta",
  "text":"<parça>"}}`. Text'i biriktir, ilk `\n` gelince kes.
- **M5 — Message_stop / usage:** son event `message_stop`; ayrıca
  `message_delta` içinde `usage` (input_tokens hariç güncel) döner.
  Usage yakalanır (011/013/015.1 uyumu için).
- **M6 — Erken kesme:** ilk `\n` bulununca stream'i **kapat**
  (`resp.close()`); kalan chunk'lar okunmaz. Böylece gerçek hız
  kazancı elde edilir.
- **M7 — Hata dallanması:** HTTP hataları streaming'te de aynı
  (`RetryAfterError` dahil); parse hatası
  `LLMPlannerError("streaming: geçersiz SSE ...")`; boş cevap
  `LLMPlannerError("boş plan cevabı")`.
- **M8 — claude/acp değişmez.**
- **M9 — Test:** +6 test — alan yok/true/tip, non-streaming
  bit-uyumlu (regresyon), streaming happy path, ilk newline'da
  kes, boş stream, HTTPError streaming'te de yakalanır.
- **M10 — DECISIONS:** [KARAR] neden opt-in; SSE parser inline;
  usage yakalanır.

## Kapsam DIŞI
- `input_json_delta` tool-use deltaları (016.1+).
- `message_start` içindeki ilk usage — final message_delta yeter.
- Async iterator — subprocess/urllib blocking yeter.

## Kısıt
- `_call_anthropic` yeni **keyword-only** `stream: bool = False`
  parametre; default False → 011/015.1 çağrıları etkilenmez.
- `_anthropic_planner` `goal.stream`'i bind.
- Türkçe hata; ruff/mypy temiz.

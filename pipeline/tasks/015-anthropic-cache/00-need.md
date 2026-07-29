# 015 — İhtiyaç: Anthropic prompt caching

## Bağlam
Anthropic Messages API `system` alanı hem string hem de bloklar
listesi kabul eder. Blok formatında `cache_control: {"type":
"ephemeral"}` verildiğinde model bu sistem promptunu 5 dakika
cache'ler; sonraki çağrılarda aynı promptu tekrar tokenize etmez
(hem hız hem maliyet indirimi). ATLAS'ta `goal.llm_prompt` uzun
sistem persona kilidi olarak kullanıldığında bu çok pratik —
her plan çağrısında aynı prompt gider.

## İhtiyaç (tek cümle)
`Goal.prompt_cache: bool = False` opsiyonel alanı ile YAML'da cache
açılabilsin; True + `llm_prompt` set edildiğinde anthropic body.system
string yerine `[{"type":"text","text":<prompt>,"cache_control":{"type":
"ephemeral"}}]` formatına dönsün.

## Ölçülebilir Başarı
- **M1 — Alan opsiyonel:** `Goal.prompt_cache: bool = False`; eski
  YAML'lar hiç değişmeden yüklenir.
- **M2 — YAML doğrulama:** bool değil → `SpecError("prompt_cache bool
  olmalı, gelen: <tip>")`.
- **M3 — Cache kapalı (varsayılan):** `system` string; body-uyumlu
  010 davranışı (bit-uyumlu regresyon).
- **M4 — Cache açık + llm_prompt yok:** `system` alanı gövdeye
  eklenmez (010 mantığı, alan yoksa hiç yazılmaz).
- **M5 — Cache açık + llm_prompt var:** `system` bloklar listesi;
  içerik `{"type":"text","text":<llm_prompt>,"cache_control":{"type":
  "ephemeral"}}`.
- **M6 — claude/acp değişmez:** iki backend cache alanını yok sayar
  (protokolde native değil). Alan yalnız anthropic'te etkin.
- **M7 — Test:** +5 test — alan yok/geçerli/tip yanlış, cache açık
  gövde formatı, cache açık ama llm_prompt yok = system yok.
- **M8 — DECISIONS:** [KARAR] tek alan (cache öncelik yok); ephemeral
  neden default type.

## Kapsam DIŞI
- Cache-hit indirim ücretlendirmesi (`cache_creation_input_tokens` vs
  `cache_read_input_tokens`) — Görev 015.1.
- Message-level cache_control (mesajlar için ayrı) — sadece system
  şu an.
- Cache-TTL uzatma (`type: "1h"`) — ephemeral (5 dk) yeter.

## Kısıt
- `Goal` yeni alan **opsiyonel default'lu** (003.2 kalıbı).
- `_call_anthropic(..., system=)` şu an sadece `str`; genişlemesi
  `str | list[dict] | None`. `_anthropic_planner` `goal.prompt_cache`
  bakar, uygun formu seçer.
- Türkçe hata; istisna adları `*Error` sonekli.

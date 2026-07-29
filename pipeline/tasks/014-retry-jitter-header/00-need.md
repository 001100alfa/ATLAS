# 014 — İhtiyaç: Retry jitter + `Retry-After` header

## Bağlam
SPEC 008 sabit üstel backoff verdi (`backoff * 2**attempt`). İki
zayıflığı var:
1. **Thundering herd:** aynı anda başlayan iki agent aynı sürede
   bekleyip aynı anda yeniden dener → sunucuya iki simetrik yük.
2. **Retry-After ihmal:** Anthropic 429/529 response'ları `Retry-After`
   başlığı (saniye) verir; kör backoff bu ipucunu görmezden gelir.

## İhtiyaç (tek cümle)
Retry sarmalayıcısı `ATLAS_LLM_JITTER=0.5` env'inde `[0, jitter)`
rastgele salınım ekleyebilsin; `_call_anthropic` `HTTPError`
yakaladığında response `Retry-After` başlığı varsa `LLMPlannerError`
mesajına `retry_after=<sn>` ekleyip iletiyor, retry sarmalayıcısı
`RetryAfterError` özel sınıfını yakalarsa **backoff yerine header
saniyesini** kullansın.

## Ölçülebilir Başarı
- **M1 — Jitter env:** `ATLAS_LLM_JITTER` (varsayılan `0.0` = kapalı).
  Değer float, negatif → 0.
- **M2 — Jitter geometrisi:** sleep = `backoff * 2**attempt + random.
  uniform(0, jitter)`. Jitter 0 → mevcut davranış (bit-uyumlu).
- **M3 — `RetryAfterError`:** `LLMPlannerError` alt sınıfı; attribute
  `retry_after_s: float`. Anthropic `HTTPError` code=429/529 +
  `Retry-After` başlığı olan yanıtlar için üretilir.
- **M4 — Retry-After öncelik:** sarmalayıcı `RetryAfterError` yakalarsa
  `_sleep(retry_after_s)` (backoff yerine); jitter yine eklenebilir
  ama header'a **saygı önceliklidir** (ilaveten değil).
- **M5 — Header formatı:** yalnız `int` saniye kabul edilir (HTTP
  tarih formatı **kapsam DIŞI** — Anthropic sadece saniye kullanır).
  Parse hatası → normal `LLMPlannerError` (backoff'a düş).
- **M6 — Non-anthropic backend'ler:** claude/acp `Retry-After`'a
  erişim yok — `RetryAfterError` hiç fırlatılmaz; jitter yine hepsine
  uygulanır (sarmalayıcı seviyesi).
- **M7 — Test:** +6 test — jitter env, 429+Retry-After parse,
  400 ama Retry-After yok, 529+Retry-After, sarmalayıcı header
  saniyesini kullanır, header parse hatası backoff'a düşer.
- **M8 — DECISIONS:** [KARAR] neden jitter opsiyonel, `RetryAfterError`
  ayrı sınıf.

## Kapsam DIŞI
- HTTP `Retry-After` tarih formatı (RFC 7231) — Anthropic saniye
  kullanır; parser kapsam dışı.
- Global retry_after cap (üst sınır) — kullanıcı env ile
  `ATLAS_LLM_TIMEOUT`'u ayarlayabilir; ayrı üst sınır YAGNI.
- Anthropic 503/504 için özel işlem — Retry-After başlığı yoksa
  normal backoff yeter.

## Kısıt
- `make_retrying_planner`, `_sleep`, `_read_retry_env` — mevcut
  sözleşmeler korunur; genişlerler.
- `_call_anthropic` sadece Retry-After algılama ekler; imzası korunur.
- `RetryAfterError` public export edilir (test için).
- Türkçe mesaj; istisna adları `*Error` sonekli.

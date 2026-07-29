# 018 — İhtiyaç: gözlem uzunluk kırpma env

## Bağlam
`_format_prompt` history'deki OBSERVE metinlerini son 3'e kırpıyor
(`_MAX_HISTORY_OBSERVES=3`) ve her birini **200 karakter** sabit
kesiyor (`o[:200]`). 200 char makul çoğu senaryoda ama bazı
görevlerde (uzun stderr, JSON dump) 200 az; çok satırlı yanıtta
"bağlam kayboluyor" hissi.

## İhtiyaç (tek cümle)
`ATLAS_LLM_OBS_CHARS` env değişkeni ile gözlem başına karakter üst
sınırı ayarlanabilsin; varsayılan 200, sınır [1, 2000].

## Ölçülebilir Başarı
- **M1 — Env okuma:** `_read_obs_chars_env()` — `ATLAS_LLM_OBS_CHARS`
  int; parse hatası → 200; aralık dışı (`<=0` veya `>2000`) → 200.
- **M2 — `_format_prompt` uygulaması:** `o[:limit]` — sabit değil,
  runtime hesaplanır. Her `_format_prompt` çağrısında env yeniden
  okunmaz (sabit performans) — `_MAX_HISTORY_OBSERVES` gibi module
  scope, ama env override runtime'da? Karar: **runtime her çağrıda**
  oku (env değişikliği anında etkili; performans etkisi ihmal).
- **M3 — Varsayılan bit-uyumlu:** env yoksa 200 — mevcut testler
  yeşil.
- **M4 — Test:** +4 test — varsayılan, env override, aralık dışı
  reset, parse hatası reset.
- **M5 — DECISIONS:** [KARAR] neden runtime oku; neden 2000 üst sınır.

## Kapsam DIŞI
- History uzunluk sayısı (`_MAX_HISTORY_OBSERVES=3`) — YAGNI (obs
  başına char yeter).
- Kırpma yerine "özet" (LLM ile) — Görev 018.1+.

## Kısıt
- `_format_prompt` imzası korunur.
- Yeni exception YOK — env yanlış → varsayılan (fail-safe).
- Türkçe hata mesajı iç mesajlar için.

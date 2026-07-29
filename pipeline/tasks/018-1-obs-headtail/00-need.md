# 018.1 — İhtiyaç: gözlem head+tail kırpma (LLM özet öncesi ara adım)

## Bağlam
SPEC 018 gözlem başına char üst sınırı env-ayarlı yaptı (`ATLAS_LLM_OBS_CHARS`
varsayılan 200). Ancak basit `o[:200]` **kuyruğu atar** — uzun stderr'ın
sonundaki hata mesajı görünmez. LLM tabanlı özetleme (018.2) pahalı;
ara adım: **head+tail keep** — başı ve sonu koru, ortayı `[... N char
atlandı ...]` işaretiyle değiştir.

## İhtiyaç (tek cümle)
`ATLAS_LLM_OBS_HEAD` (varsayılan 100) + `ATLAS_LLM_OBS_TAIL` (varsayılan
100) env'leri ile gözlem `head + "\n[... N char atlandı ...]\n" + tail`
formatında sıkıştırılsın; head+tail toplamı `ATLAS_LLM_OBS_CHARS`
sınırına eşit değilse mevcut 018 davranışı korunur.

## Ölçülebilir Başarı
- **M1 — Env okuma:** `_read_obs_head_tail_env()` — head + tail
  int, parse hatası → (100, 100). Negatif → 0.
- **M2 — Uygulama:**
  - `len(obs) <= obs_chars` → dokunma (bit-uyumlu).
  - `head + tail == 0` → 018 davranışı (`o[:obs_chars]`).
  - Yoksa `head_part = obs[:head]; tail_part = obs[-tail:]`;
    atlanan = `len(obs) - head - tail`; ara = `[... N char atlandı ...]`.
- **M3 — Sınır kontrolü:** `head + tail > obs_chars` → 018 davranışı
  (tail atla, head'e kırp; kullanıcı env'i mantıksız verirse
  bir davranış olsun).
- **M4 — Test:** +5 test — env yok davranış 018, head+tail parse,
  kısa obs dokunulmaz, uzun obs head+tail bölünür, mantıksız env
  → 018 fallback.
- **M5 — DECISIONS:** [KARAR] neden ara adım; LLM özetleme neden 018.2.

## Kapsam DIŞI
- LLM ile gerçek özetleme — Görev 018.2 (ekstra LLM çağrısı + cost).
- Semantik akıllı kırpma (JSON, XML parser) — YAGNI.
- Tail'da satır sınırlarında kırpma — basit char yeter.

## Kısıt
- `_format_prompt` imzası korunur.
- Env okuma runtime (018 kalıbı) — env değişikliği anında etkili.
- Türkçe atlama mesajı.

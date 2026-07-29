# 011 — İhtiyaç: Token cost (report-only)

## Bağlam
Anthropic Messages API response gövdesinde `usage.input_tokens` ve
`usage.output_tokens` alanları vardır — her çağrının maliyeti
somut token değeriyle bilinir. Şu an ATLAS bunu görmezden gelmiyor
ama bir yere de yazmıyor; kullanıcı ne kadar token yaktığını manuel
Anthropic panelinden takip etmek zorunda.

Bu görev, **rapor-mu-tek** kapsamda usage bilgisini yakalar:
- stderr'a insan-okunur trace satırı yaz
- audit'e denetim izi olarak kaydet

**CallBudget entegrasyonu kapsam DIŞI** — soyut kredi modeli değişmez.
Görev 013'te gerçek token→kredi dönüşümü ele alınır (retry ile birlikte).

## İhtiyaç (tek cümle)
`ATLAS_LLM_TRACE=1` env'inde her başarılı anthropic çağrısı sonrası
stderr'a `[llm] anthropic tokens: in=N out=N cost≈$X.XXXX` yazılsın;
`ATLAS_LLM_PRICE_IN`/`ATLAS_LLM_PRICE_OUT` (per million token, USD)
varsa cost hesaplansın, yoksa `cost≈?`.

## Ölçülebilir Başarı
- **M1 — Anthropic usage parse:** response `data["usage"]` içindeki
  `input_tokens` ve `output_tokens` yakalanır. Yoksa `0`.
- **M2 — Trace açık formatı:** `[llm] anthropic tokens: in=<n> out=<n>
  cost≈$<f>` (fiyat env'i varsa) veya `cost≈?` (env yoksa).
- **M3 — Trace kapalı:** `ATLAS_LLM_TRACE` set edilmemişse veya `1`
  değilse stderr'a hiçbir şey yazılmaz.
- **M4 — Fiyat hesabı:** `cost = in * price_in / 1e6 + out * price_out
  / 1e6` (per million token USD). 6 ondalık basamak.
- **M5 — claude/acp:** iki backend usage yayınlamaz (protokolde native
  usage yok) → hiçbir trace yazılmaz.
- **M6 — Sözleşme değişmez:** `_call_anthropic` yine `str` döner.
  Usage side-channel'da (stderr) veya (opsiyonel Görev 013+) audit.
- **M7 — Test:** +5 test — anthropic usage yakalar, format doğru,
  cost hesabı, env yoksa, trace kapalı.
- **M8 — DECISIONS:** [KARAR] neden report-only; CallBudget entegrasyonu
  neden 013'te.

## Kapsam DIŞI
- CallBudget'a token maliyeti işlenmesi — Görev 013.
- Otomatik quota kesme (bütçe aşımı → LLM çağrısı durmaz) — Görev 013.
- ACP usage — protokol native değil, agent-özel; ertelendi.
- Prompt caching (Anthropic) — Görev 015+.
- Multiple model pricing tablosu — env yolu yeter (kullanıcı
  seçtiği modelin fiyatını girer).

## Kısıt
- `Planner`, `_call_anthropic`, `_anthropic_planner` **imzaları
  korunur**. Trace yalnız yan-etki.
- stdlib-only.
- Türkçe metin (trace prefix'i tutarlı olsun diye `[llm]` sabit).
- Fiyat env parse hatası → varsayılan `?` (fail-safe).

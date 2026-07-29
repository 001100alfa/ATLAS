# 025 — İhtiyaç: `skills/engineering/prompt/SKILL.md`

## Bağlam
CLAUDE.md `skills/engineering/` ve `skills/trading/` alanlarına
işaret ediyor; ancak prompt engineering için özel bir SKILL.md yok.
Görevler prompt yazarken tekrar tekrar deneyip yanılıyor; kullanıcı
LLM'e görev-tipi bazlı iyi prompt kalıpları arıyor.

## İhtiyaç (tek cümle)
`skills/engineering/prompt/SKILL.md` — göreve başlamadan okunacak
prompt engineering rehberi: görev-tipi kalıpları (kod yaz, test yaz,
DXF üret, EN 1993 doğrulama), ATLAS-özel örnekler (Goal.llm_prompt),
karşı örnekler ("bunu yapma" kısmı).

## Ölçülebilir Başarı
- **M1 — Dosya:** `skills/engineering/prompt/SKILL.md` — Türkçe,
  yapılandırılmış Markdown.
- **M2 — Bölümler:**
  1. Sistem promptu vs kullanıcı promptu (`Goal.llm_prompt` vs
     `Goal.goal`) — ne nereye gider.
  2. Görev-tipi kalıpları:
     - **Kod yazma**: dosya yolu ver, format, dil, çıktı kısıtı.
     - **Test yazma**: framework, kapsam, edge case listesi.
     - **DXF üret**: birimler (mm), koordinat sistemi, katman.
     - **EN 1993 doğrulama**: sınır durumu, güvenlik faktörleri.
  3. ATLAS-özel: `plan_kind: llm` + `action_allowlist: [write]`
     senaryosu; plan çıktı sözleşmesi (`fiil:arg1[:arg2]`).
  4. Karşı örnekler: çok geniş prompt, birim eksik, çıktı formatı
     belirsiz.
  5. Prompt caching (`prompt_cache: true`) ne zaman kullanılır.
- **M3 — 300-500 satır** — geniş rehber ama biryerden okunabilir.
- **M4 — Kod değil, dokümantasyon:** test yok, `ruff`/`mypy` konu
  değil.
- **M5 — DECISIONS:** [KARAR] neden Türkçe; kim okuyacak.

## Kapsam DIŞI
- Örnek YAML fixture'ları (bunlar tests/goals altında zaten var).
- Otomatik prompt üretici — YAGNI.
- Multi-modal (görüntü/ses) — YAGNI.

## Kısıt
- Dokümantasyon dosyası; test/coverage kapsamı YOK.
- Türkçe; teknik terimler İngilizce korunabilir.

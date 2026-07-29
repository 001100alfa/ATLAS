# 025 — Ship

## Sonuç
`skills/engineering/prompt/SKILL.md` yazıldı — 250+ satır Türkçe
prompt engineering rehberi:

- Sistem promptu vs kullanıcı promptu ayrımı (`Goal.llm_prompt` vs `Goal.goal`)
- Görev-tipi kalıpları: kod, test, DXF, EN 1993
- ATLAS plan çıktı sözleşmesi (`fiil:arg1[:arg2]`)
- Karşı örnekler (çok geniş prompt, birim eksik, format belirsiz)
- Prompt caching, model seçimi, streaming ne zaman
- Retry & jitter env kombinasyonları
- Cost izleme workflow: doctor → dry-run → run → metrics → dashboard
- Öz-denetim adımları

Test/coverage yok — dokümantasyon dosyası.

## Dosyalar
```
skills/engineering/prompt/SKILL.md        (yeni, ~250 sat rehber)
pipeline/tasks/025-prompt-engineering-skill/*.md   (5 artefakt)
```

## Sözleşme değişmezliği
- Sadece dokümantasyon ekleme; kod dokunulmadı.
- Test suite değişmez (505 → 533 önceki turdan).

## Kalite kapıları
- pytest: değişmedi (dokümantasyon)
- mypy/ruff: konu değil
- İçerik: mevcut SPEC'lere birebir referanslı

## Branch
`feat/025-prompt-engineering-skill` — 019.1 üstünde tek commit.

# 06 — Onay Kapısı  `/approve-spec`

**Amaç:** Kullanıcı onayını almak ve durumu ONAYLI'ya çekmek.

| | |
|---|---|
| **Girdi** | Açık soruları kapanmış spec |
| **Çıktı** | SPEC-XXX.md Durum: ONAYLI + onay kaydı |

## Prosedür
1. Spec'i kullanıcıya ÖZET + tam metin olarak sun.
2. Onay açık ifade olmalı; sessizlik onay DEĞİLDİR.
3. Onay tarihi ve kapsamı spec'e işlenir. Değişiklik = re-onay.

## Kapıya Katkısı
Gate: 'kullanıcı onayı alındı' — build kilidi açılır.

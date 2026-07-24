# Mimari Karar Kayıtları (ADR)

Büyük/geri-dönüşü zor mimari kararlar buraya birer ADR dosyası olarak yazılır.
Küçük kararlar `DECISIONS.md`'de `[KARAR]` etiketiyle tutulur.

## Format
Dosya adı: `NNNN-kisa-baslik.md` (ör. `0001-juggler-on-yuz.md`).
Şablon:

```markdown
# NNNN — Başlık
Durum: Önerildi | Kabul | Reddedildi | Yerini aldı: NNNN
Tarih: YYYY-MM-DD

## Bağlam
Kararı gerektiren durum, kısıtlar.

## Karar
Ne seçildi.

## Sonuçlar
Artılar, eksiler, takaslar; etkilenen bileşenler.
```

## Kayıtlı ADR'ler
Henüz ayrı ADR dosyası yok — mevcut mimari kararlar `DECISIONS.md` ve
`docs/ARCHITECTURE.md`'de. İlk resmi ADR gerektiğinde `0001-...md` ile başlar.

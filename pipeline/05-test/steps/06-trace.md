# 06 — İzlenebilirlik Matrisi  `/trace`

**Amaç:** FR <-> test eşlemesini kanıtlamak + tester subagent koşusu.

| | |
|---|---|
| **Girdi** | Tüm testler |
| **Çıktı** | TEST-XXX.md (FR-test tablosu + subagent raporu) |

## Prosedür
1. Tabloyu doldur: her FR >= 1 test, her test >= 1 FR.
2. Eşleşmeyen test = kapsam dışı iş sinyali -> drift-check'e bildir.
3. tester subagent'ı BAĞIMSIZ koştur, raporunu ekle.

## Kapıya Katkısı
Gate: izlenebilirlik tablosu tam.

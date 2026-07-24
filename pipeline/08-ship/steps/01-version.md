# 01 — Sürüm Kararı  `/version`

**Amaç:** SemVer'e göre doğru sürüm numarasını seçmek.

| | |
|---|---|
| **Girdi** | Diff + CHANGELOG |
| **Çıktı** | vX.Y.Z kararı + pyproject güncellemesi |

## Prosedür
1. Kırıcı değişiklik var mı? (imza/davranış) -> MAJOR.
2. Yeni özellik -> MINOR. Sadece düzeltme -> PATCH.
3. Emin değilsen kırıcıdır — MAJOR seç, gerekçele.

## Kapıya Katkısı
Sürüm anlamı korunur.

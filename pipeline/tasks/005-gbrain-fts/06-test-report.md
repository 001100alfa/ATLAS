# 005 — Test Raporu

| Metrik | Değer |
|---|---|
| Toplam pytest | **286/286** ✅ (267 + 19 yeni) |
| Yeni test | 24 (11 index + 8 fts entegrasyon + 5 CLI reindex/recall/context) |
| Coverage | **%95** (gate ≥ %90) |
| mypy --strict | **25 dosya** temiz |
| ruff | temiz |
| Regresyon | test_platform, test_core (33 test) — hepsi yeşil, GBrain sözleşmesi korundu |

## Kabul Kriterleri
| # | Test | Durum |
|---|---|---|
| AC1 happy recall | `test_recall_fts_happy` | ✅ |
| AC2 stale auto reindex | `test_recall_stale_otomatik_reindex` | ✅ |
| AC3 mtime hilesi | `test_mtime_hilesi_hash_yakalar` | ✅ |
| AC4 silinen not | `test_recall_silinen_not_donmez` | ✅ |
| AC5 graf komşusu | `test_recall_graf_komsusu` | ✅ |
| AC6 fallback | `test_recall_fallback_fts_yoksa` | ✅ |
| AC7 CLI reindex | `test_reindex_partial`, `test_reindex_full` | ✅ |
| AC8 regresyon | test_platform (12) + test_core (21) yeşil | ✅ |
| AC9 200-not smoke | `test_performans_200_not_smoke` (< 500 ms) | ✅ |

# 005 — PLAN

## WBS
| # | Adım | Çıktı | Gate |
|---|---|---|---|
| 3.1 | `gbrain_index.py`: şema + `ensure_fresh` + `upsert` + `search` + `is_fts_available` | src/atlas_core/memory/gbrain_index.py, tests/test_gbrain_index.py | pytest yeşil |
| 3.2 | `gbrain.py` entegrasyonu (opsiyonel index_path + FTS yolu + fallback) | src/atlas_core/memory/gbrain.py edit, tests/test_gbrain_fts.py | AC1–AC6 yeşil; test_platform regresyon |
| 3.3 | CLI `atlas reindex` | cli.py edit, tests/test_cli_direct.py'a 3 test | in-process test yeşil |
| 3.4 | Kalite | mypy strict + ruff + coverage ≥ %90 | full gate yeşil |
| 3.5 | Ship | test-report + ship + DECISIONS + commit | manuel doğrulama |

## Risk
| # | Risk | Azaltma |
|---|---|---|
| R1 | FTS5 varsayılan tokenizer Türkçe'yi kırar | `unicode61 remove_diacritics 2` — Türkçe için yeterli; ayrıca sqlite/fts5 yoksa fallback var |
| R2 | Windows'ta sqlite dosya kilitlenmesi (paralel test) | Her test kendi tmp_path'inde bağımsız DB kullanır |
| R3 | `Vault.graph()` her ensure_fresh'te tüm .md okur — indeks amacına aykırı | Graf sadece reindex tetiklendiğinde okunur; sonuç bellekte tutulmaz (recall her seferinde stale-check ile karar verir) |
| R4 | mypy sqlite3 stub'ları | sqlite3 stdlib, tip zaten var; Row → tuple[Any] cast net tutulur |
| R5 | Mevcut `Recall.score` numerik semantiği değişir | FTS bm25 normalize edilir; testte skor > 0 kontrolü (kesin değer değil) |

## Rollback
Adım commit'leri atomik; gate düşerse `git reset --hard HEAD~1` (onay).
Fallback tasarımı sayesinde en kötü senaryoda GBrain eski davranışına düşer.

# 005 — Ship

## Sonuç
GBrain artık SQLite FTS5 önbelleğiyle çalışıyor:
- `recall()` FTS bm25 + graf komşuluğu — mevcut `Recall` sözleşmesi korundu.
- Stale tespiti (mtime + sha256) `recall()` başında otomatik reindex tetikler.
- `remember()` yazma yolunda deterministik `upsert` yapar.
- `atlas reindex [--full]` manuel kapı.
- FTS5 yoksa (eski sqlite) otomatik fallback O(N·M) yola düşer, uyarı verir.
- Vault gerçek kaynak — indeks silinse bile bilgi kaybı yok.

## Dosyalar
```
src/atlas_core/memory/gbrain_index.py         (yeni, 180 satır)
src/atlas_core/memory/gbrain.py               (edit: FTS/fallback dallanma)
src/atlas_core/cli.py                         (edit: reindex subcommand)
tests/test_gbrain_index.py                    (11)
tests/test_gbrain_fts.py                      (8)
tests/test_cli_direct.py                      (+5)
pipeline/tasks/005-gbrain-fts/*.md            (4 artefakt)
```

## Sözleşme Değişmezliği
- `GBrain.recall/remember/context_for/log_event` imzaları korundu.
- `GBrain.__init__` **genişletildi** (opsiyonel `index_path`) — eski
  `GBrain(vault_root)` çağrıları aynen çalışır.
- `Recall` dataclass alanları (name/score/snippet) korundu.
- `Vault` API'sine dokunulmadı.

## Performans
200 sentetik notta `recall("sabit")` < 500 ms (test smoke).
Gerçek vault (7 not) < 5 ms. Mevcut O(N·M) yaklaşımdan asimptotik
kazanç: not sayısı arttıkça FTS avantajı büyür.

## Branch & Commit
Branch: `feat/005-gbrain-fts` — tek commit.

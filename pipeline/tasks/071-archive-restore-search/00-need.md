# Görev 071 — İhtiyaç

SPEC 065 `--search PATTERN` içerik arıyor (list-only). SPEC 033 `--restore
<id>` explicit task_id gerektiriyor. Kullanıcı "bu dosyayı içeren
arşivi geri aç" derse iki komut çağırıyor:
```
atlas archive --search 09-ship          # → task-042
atlas archive --restore task-042 --apply
```
Birleşim komutu: `atlas archive --restore --search 09-ship`.

## Kabul

- `atlas archive --restore --search PATTERN [--apply]`:
  - `--restore` bayraksız (nargs="?" const="") + `--search PATTERN`.
  - `--search` arşiv-arama; tek eşleşme → arşiv adından task_id çıkar
    (`<task_id>-YYYY-MM-DD.tar.gz` → `<task_id>`).
  - 0 eşleşme → exit 6 (SPEC 033 arşiv bulunamadı sınıfı).
  - 2+ eşleşme → exit 2 (belirsizlik; kullanıcı --search daraltmalı,
    stderr'e eşleşen arşiv listesi).
  - Regex geçersiz → exit 2.
- `--restore <id>` (search yok) SPEC 033 BİT-UYUMLU.
- `--search PATTERN` (restore yok) SPEC 065 BİT-UYUMLU.
- Dispatcher sırası: `--restore` (varsa) → search-based veya id-based
  restore. Sonra `--search` list-only.

## Risk

- Arşiv adı formatı `<task_id>-YYYY-MM-DD.tar.gz` — kesme `-11` char
  (`-YYYY-MM-DD` uzunluk). Farklı formatta arşiv varsa fallback stem.

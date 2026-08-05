# Görev 075 — İhtiyaç

Kullanıcı `archive/` dizininde ne olduğunu görmek için `ls archive/`
yapıyor — sadece isimler. Task_id/date/size/member_count metadata'yı
manuel `tar tzf` ile eşleştirmek zor. `atlas archive --list` doğal
tamamlama (SPEC 037.2 `ai-cli list` kalıbı).

## Kabul

- `atlas archive --list [--json] [--archive-root]`.
- Her arşiv için: `{archive, task_id, date, size_bytes, size_human,
  member_count, mtime}`.
- Format `<task_id>-YYYY-MM-DD.tar.gz` — atipik format fallback stem.
- Bozuk tar → `member_count=-1` (skip'lemez, göster).
- Deterministik sıra (alfabetik).
- `--json` bit-hassas; insan çıktısı hizalı tablo.
- Dispatcher: `--list` en önde (read-only, yıkıcı işlemlerden önce).

## Risk

- Büyük arşivlerde `getnames()` yavaş olabilir; SPEC 065 aynı kalıp,
  tolere ediliyor.

# 017 — İhtiyaç: `atlas archive --auto` yaş filtresi

## Bağlam
SPEC 012 `atlas archive --all` her `09-ship.md` içeren görevi
arşivliyor — yaş gözetmeksizin. Bir görev bitmiş ama SHIP dokümanı
henüz "taze" olduğunda kullanıcı belki henüz arşive taşımak istemez;
tarihçe açık kalsın. Cron/hook senaryosunda "N günden eski görevleri
otomatik arşivle" ihtiyacı var — kullanıcı `atlas archive --all
--auto --apply --yes` diyerek batch iş verebilsin.

## İhtiyaç (tek cümle)
`atlas archive --all --auto` verildiğinde adaylar `09-ship.md`
mtime'ı `ATLAS_ARCHIVE_AGE_DAYS` (varsayılan 7) gün öncesinden
eski olanlar; taze görevler atlanır.

## Ölçülebilir Başarı
- **M1 — Flag:** `--auto` bool bayrağı `--all` ile kullanılır
  (`--auto --all değil` → uyarı yok, sessizce yok sayılır çünkü
  tek görev yolu yaş filtresine ihtiyaç duymaz).
- **M2 — Yaş eşiği:** `ATLAS_ARCHIVE_AGE_DAYS` env (varsayılan 7);
  parse hatası → 7 (fail-safe).
- **M3 — Yaş hesabı:** görev `09-ship.md` dosyasının `st_mtime`
  şu andan `age_days` gün eskiden büyükse aday. Yeni ship.md'li
  taze görev atlanır.
- **M4 — Dry-run çıktı:** `[dry-run] toplu arşivleme adayları (auto,
  >7 gün): N görev`. Yaş bilgisi başlıkta.
- **M5 — 012 uyum:** `--all` mevcut yolu (yaş yok) korunur —
  `--auto` yoksa tüm ship.md'liler seçilir (mevcut davranış).
- **M6 — Çift kapı korunur:** `--auto --apply --yes` üçlü — çift
  onay yaş filtresine rağmen istenir (yıkıcı iş yıkıcı).
- **M7 — Test:** +4 test — dry-run yaş filtresi, eski görev seçilir,
  taze atlanır, env override.
- **M8 — DECISIONS:** [KARAR] neden `mtime` (ctime değil);
  varsayılan 7 gün.

## Kapsam DIŞI
- Cron/hook script'i (Windows Görev Zamanlayıcı, `cron`) — sadece
  komut var; kullanıcı sistem zamanlayıcısıyla bağlar. Belge Görev
  017.1'de.
- Yaş üst-sınır (`--max-age`) — YAGNI.
- Yaş yerine tarih penceresi (`--since 2026-01-01`) — YAGNI.

## Kısıt
- 012 `--all` yolu **hiç değişmez** — `--auto` yeni bir daraltma.
- `_iter_archive_candidates(tasks_root)` `age_days` parametresi
  alacak; `None` (varsayılan) → 012 davranışı.
- Türkçe rapor.

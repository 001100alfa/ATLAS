# Görev 086 — İhtiyaç

SPEC 080 `.atlas/doctor-history/` tarihçesi var. Kullanıcı `--diff PATH`
ile karşılaştırma için önce `_list_doctor_history` çalıştırıp PATH
bulmak zorunda. Doğal "N. eski snapshot ile karşılaştır" bayrağı yok.

## Kabul

- `atlas doctor --diff-history N` (int, 1-based, en yeni=1).
- `_list_doctor_history()` çıktısı date desc → `N=1` en yeni,
  `N=len` en eski.
- `N < 1` → SPEC HATASI exit 2.
- `N > len(history)` → SPEC HATASI exit 2 (mesajda len).
- Tarihçe boş → SPEC HATASI exit 2 ("İlk kalibrasyon için: atlas doctor
  --save-baseline" öneri).
- `--diff-history` + `--diff` MUTEX exit 2 (kaynak belirsiz).
- `--diff-history` + `--auto-baseline` MUTEX exit 2.
- Seçilen snapshot path'i `diff_baseline_arg`'a atanır → mevcut
  `_diff_doctor_reports` yolu çalışır (BİT-UYUMLU).
- JSON çıktıda snapshot metadata (path/date) eklenmez (delta şeması
  SPEC 057 AYNI).

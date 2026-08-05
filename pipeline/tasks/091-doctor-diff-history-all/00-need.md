# Görev 091 — İhtiyaç

SPEC 086 `--diff-history N` tek snapshot ile mevcut arası delta gösterir.
Kullanıcı "trend" görmek için N=1,2,3... hepsini tek tek çalıştırıyor.
Toplu bakış için `--diff-history-all` (tüm tarihçe ↔ mevcut toplu diff
tablosu) gerek.

## Kabul

- `atlas doctor --diff-history-all [--json]`.
- Her `.atlas/doctor-history/baseline-*.json` snapshot ile mevcut rapor
  arası delta.
- Sıra: date desc (en yeni önce; N=1 kalıbı ile simetrik).
- Pretty tablo: `date | +warn | -warn | Δquality`.
- JSON: `{snapshots: [{date, path, delta: {SPEC 057 şeması}}]}`.
- Tarihçe boş → SPEC HATASI exit 2 (SPEC 086 kalıbı).
- MUTEX: `--diff`, `--auto-baseline`, `--save-baseline`,
  `--diff-history` (N) ile aynı çağrıda kullanılamaz → exit 2.
- `--serve/--schema/--format prometheus` ile MUTEX (SPEC 057 kalıbı).
- Sağlık kontrolü YAPILIR (mevcut rapor gerekli); ancak diff çıktısı
  MUTEX üzerine yaz.

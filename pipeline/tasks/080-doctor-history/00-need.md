# Görev 080 — İhtiyaç

SPEC 062 `--save-baseline` tek dosya (default `.atlas/doctor-baseline.json`)
üzerine yazar. Kullanıcı tarihçe (kronoloji) görmek isterse eski
snapshot'lar kayboluyor. SPEC 057 `--diff` için "geçmişe dönme"
mümkün değil.

## Kabul

- `--save-baseline` (default path) → **BONUS**:
  `.atlas/doctor-history/baseline-<today>.json` da yazılır.
- Custom `--save-baseline PATH` → SADECE PATH (tarihçe YOK; bilinçli).
- `--history-keep N` → tarihçe retention (mtime yerine date-based
  sort; en yeni N tutar).
- `--history-list [--json]` → sağlık kontrolü YAPMA (kısa devre),
  yalnız listele.
- `--history-keep < 1` → exit 2.

## Değişmezlik

- SPEC 062 `--save-baseline` default path tek dosya → **çift dosya**
  (yeni yan etki). Bit-uyumluluk: dış tüketici sadece default path'i
  okuyor → aynı içerik.
- SPEC 057 `--diff` / SPEC 062 `--auto-baseline` BİT-UYUMLU (default
  path aynı).

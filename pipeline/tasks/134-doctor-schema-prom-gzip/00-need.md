# Görev 134 — İhtiyaç

SPEC 128 `doctor --schema --format prometheus` info-metric ailesini
stdout'a basar. CI artifact / gzip storage için `--out PATH --gzip`
gerek (SPEC 110/114 kalıbı, --schema kısa devre için).

## Kabul

- `atlas doctor --schema --format prometheus --out PATH [--gzip]`.
- --schema kısa devre içinde ele alınır (SPEC 040 kalıp korunur).
- --out yalnız `--schema + --format prometheus` VEYA
  `--diff-history-all + --format prometheus` ile anlamlı; --schema
  bloğunda yeni `--out` desteği. Diğer schema modları (JSON) `--out`
  desteklemez → SPEC HATASI exit 2.
- --gzip yalnız --out ile → aksi exit 2 (mevcut kontrol kalıbı).
- Auto-suffix `.gz` (SPEC 103/108/109/111/114 kalıbı).
- Dosya içeriği stdout modu ile BİT-UYUMLU (decompress kontrolü).
- --out YOKSA SPEC 128 stdout AYNI.

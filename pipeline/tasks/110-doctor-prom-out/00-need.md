# Görev 110 — İhtiyaç

SPEC 104 `doctor --diff-history-all --format prometheus` stdout'a
grup metrikleri basar. CI artifact / prometheus scrape endpoint dosya
için `--out PATH` gerek (SPEC 096/105 kalıbı).

## Kabul

- `atlas doctor --diff-history-all --format prometheus --out PATH`.
- `--out` yalnız `--diff-history-all + --format prometheus` ile
  anlamlı → aksi SPEC HATASI exit 2.
- Parent auto-mkdir; IO hatası exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU.
- `--strict` ile ORTOGONAL (SPEC 097 exit 9 korunur; dosyaya yazılır).
- `--gzip` YOK (bu tur; ayrı SPEC 111 kalıbı ileride eklenebilir).
- `--out` VERİLMEZSE SPEC 104 stdout AYNI.

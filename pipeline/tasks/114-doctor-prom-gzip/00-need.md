# Görev 114 — İhtiyaç

SPEC 110 `doctor --diff-history-all --format prometheus --out PATH` düz
metin. `--gzip` (SPEC 103/108/109/111 kalıbı) artifact boyutu için.

## Kabul

- `atlas doctor --diff-history-all --format prometheus --out PATH --gzip`.
- `--gzip` yalnız `--out` ile → aksi exit 2.
- Auto-suffix `.gz`; sahipse aynen.
- Decompress → SPEC 110 düz metin BİT-UYUMLU.
- `--gzip` YOKSA SPEC 110 düz metin AYNI.

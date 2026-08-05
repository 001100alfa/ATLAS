# Görev 109 — İhtiyaç

SPEC 106 `ai-cli list --outdated --json-lines --out PATH` düz NDJSON.
`--gzip` bayrağı (SPEC 103/108 kalıbı) artifact boyutu için.

## Kabul

- `atlas ai-cli list --outdated --json-lines --out PATH --gzip`.
- `--gzip` yalnız `--out` ile → aksi exit 2.
- Auto-suffix `.gz`; sahipse aynen (SPEC 103 kalıbı).
- Decompress → SPEC 106 düz NDJSON BİT-UYUMLU.
- `--strict` ile ORTOGONAL (exit 4 korunur, gzip'e yazılır).

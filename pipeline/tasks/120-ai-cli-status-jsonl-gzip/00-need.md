# Görev 120 — İhtiyaç

SPEC 118 `ai-cli status --json-lines --out PATH` düz NDJSON.
`--gzip` (SPEC 103/108/109/111/114 kalıbı) artifact boyutu için.

## Kabul

- `atlas ai-cli status <name> --json-lines --out PATH --gzip`.
- `--gzip` yalnız `--out` ile → aksi exit 2.
- Auto-suffix `.gz`; sahipse aynen.
- Decompress → SPEC 118 düz NDJSON BİT-UYUMLU.
- `--gzip` YOKSA SPEC 118 düz metin AYNI.

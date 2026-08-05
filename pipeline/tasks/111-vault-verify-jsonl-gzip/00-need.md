# Görev 111 — İhtiyaç

SPEC 092 `vault verify --format json-lines --out PATH` düz NDJSON.
Büyük vault'lar için binlerce broken link satırı → gzip artifact/
storage için gerek.

## Kabul

- `atlas vault verify --format json-lines --out PATH --gzip`.
- `--gzip` yalnız `--out` ile → aksi exit 2 (SPEC 103/108/109 kalıbı).
- Auto-suffix `.gz`; sahipse aynen.
- Decompress → SPEC 092 düz NDJSON BİT-UYUMLU.
- `--strict` ORTOGONAL (exit 4 korunur; gzip'e yazılır).

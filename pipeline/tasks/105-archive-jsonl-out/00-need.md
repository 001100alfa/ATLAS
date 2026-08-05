# Görev 105 — İhtiyaç

SPEC 098 `--list --json-lines` stdout'a NDJSON basıyor. CI'de artifact
olarak dosyada saklamak için `> file.jsonl` shell redirect gerek —
Windows kodlaması + atomic write garantisi yok. SPEC 092/096 `--out`
kalıbı archive tarafında da uygulanmalı.

## Kabul

- `atlas archive --list --json-lines --out PATH`.
- `--out PATH` yalnız `--json-lines` ile birlikte anlamlı → aksi
  SPEC HATASI exit 2 (SPEC 092 kalıbı).
- Parent dir auto-mkdir.
- Yazma hatası → SPEC HATASI exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU.
- `--out` verildiğinde stdout NDJSON basmaz.
- `--out` VERİLMEZSE SPEC 098 BİT-UYUMLU (stdout stream).

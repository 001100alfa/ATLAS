# Görev 139 — İhtiyaç

SPEC 132 `metrics --alert-history-show` stdout'a basar. CI artifact ve
retro post-mortem için dosyaya yaz gerek (SPEC 105/106 kalıbı).

## Kabul

- `atlas metrics --alert-history-show [PATH] --out PATH --json`.
- `--out` yalnız `--json` ile birlikte anlamlı (pretty tablo dosyaya
  yazılmaz — SPEC 105 kalıbıyla simetrik). Aksi → SPEC HATASI exit 2.
- Parent auto-mkdir; yazma hatası → SPEC HATASI exit 2.
- Dosya içeriği stdout `--json` modu ile BİT-UYUMLU (NDJSON + summary).
- `--out` verildiğinde stdout NDJSON basmaz.
- `--out` VERİLMEZSE SPEC 132 stdout AYNI.

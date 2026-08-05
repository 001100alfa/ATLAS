# Görev 106 — İhtiyaç

SPEC 099 `ai-cli list --outdated --json-lines` stdout'a stream. CI'de
artifact dosya için `--out PATH` bayrağı gerek (SPEC 092/096/105 kalıbı).

## Kabul

- `atlas ai-cli list --outdated --json-lines --out PATH`.
- `--out` yalnız `--json-lines` ile birlikte anlamlı → aksi exit 2.
- Parent auto-mkdir; yazma hatası exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU.
- `--strict` ile ORTOGONAL (bulgu + strict + out → exit 4, dosyaya
  yazılır).
- `--out` VERİLMEZSE SPEC 099 stdout AYNI.

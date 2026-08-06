# Görev 138 — İhtiyaç

SPEC 133 `archive --restore --json-lines` stdout stream. CI pipeline
için dosyaya (SPEC 105/106/139 kalıbı) `--out PATH` gerek.

## Kabul

- `atlas archive --restore <id> --json-lines --out PATH [--apply]`.
- `--out` yalnız `--json-lines` ile → aksi SPEC HATASI exit 2.
- Parent auto-mkdir; yazma hatası → exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU (plan+summary dry-run;
  plan+restored+summary apply).
- Hata (RestoreError) → dosya YAZILMAZ, stderr; rc 3/6 korunur.
- `--out` YOKSA SPEC 133 stdout AYNI.

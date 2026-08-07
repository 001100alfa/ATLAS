# Görev 145 — İhtiyaç

SPEC 140 `vault verify --schema --format prometheus` stdout info-metric
basar. CI artifact için `--out PATH [--gzip]` (SPEC 134 kalıbı).

## Kabul

- `atlas vault verify --schema --format prometheus --out PATH [--gzip]`.
- `--out` `--schema + --format prometheus` yolunda anlamlı; JSON
  --schema modunda `--out` mevcut MUTEX (SPEC 092: json-lines gerek)
  → `--schema` özel: `--out` yalnız Prometheus dalında geçerli.
- Parent auto-mkdir; IO exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU.
- Auto-suffix `.gz`.
- `--out` YOKSA SPEC 140 stdout AYNI.

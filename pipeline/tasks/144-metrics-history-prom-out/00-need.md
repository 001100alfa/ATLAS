# Görev 144 — İhtiyaç

SPEC 143 `metrics --alert-history-show --format prometheus` stdout'a
info-metric ailesi basar. CI artifact / Grafana file_sd için `--out
PATH` gerek (SPEC 096/134 kalıbı).

## Kabul

- `atlas metrics --alert-history-show --format prometheus --out PATH`.
- `--out` yalnız `--json` VEYA `--format prometheus` (alert-history-show
  modunda) ile birlikte anlamlı → aksi SPEC HATASI exit 2.
- Parent auto-mkdir; IO hatası exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU.
- `--gzip` (SPEC 103 kalıbı) opsiyonel: `.gz` auto-suffix.
- `--out` YOKSA SPEC 143 stdout AYNI.

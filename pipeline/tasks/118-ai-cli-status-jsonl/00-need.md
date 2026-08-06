# Görev 118 — İhtiyaç

SPEC 037.4 `ai-cli status <name> [--json]` tek dict rapor. CI/scripting
için NDJSON stream + dosya yazımı gerek (SPEC 099/106 kalıbı).

## Kabul

- `atlas ai-cli status <name> --json-lines [--out PATH]`.
- `--json-lines` yalın: her alan bir satır `{"field":..,"value":..}`
  (name/installed/declared/up_to_date/install_dir/size_bytes/size_human/
  bin_path) + son satır `{"type":"summary","name":..,"up_to_date":..}`.
- `--json-lines` + `--json` MUTEX exit 2.
- `--out PATH` yalnız `--json-lines` ile → aksi exit 2 (SPEC 106 kalıbı).
- Parent auto-mkdir; IO hatası exit 2.
- `--json-lines` YOKSA SPEC 037.4 BİT-UYUMLU.

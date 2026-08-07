# Görev 146 — İhtiyaç

SPEC 037.4 `ai-cli status <name>` her paket için detaylı rapor.
SPEC 040 (doctor) + SPEC 136 (vault verify) `--schema` kalıbı ai-cli
status için de gerek — JSON şeması dokümante ve makine-okunur.

## Kabul

- `atlas ai-cli status --schema [--pretty]`.
- `name` positional argument YOKSA (--schema modunda) kabul edilir
  (nargs="?"). Aksi hâlde argparse required.
- Vault gerekmez, package.json okumaz — kısa devre.
- JSON: `{schema_version, top_level:[{name,type,desc}], exit_codes,
  formats:[{name,spec,desc}], notes}`.
- top_level alanları: name/installed_version/declared_version/
  up_to_date/install_dir/size_bytes/size_human/bin_path (8 alan).
- exit_codes: 0/2/4 (SPEC 037.4/094 kalıp).
- formats: human/json/json-lines/prometheus (mevcut + gelecek).
- `--pretty` indent=2.
- `--schema` YOKSA SPEC 037.4 normal status davranışı AYNI.

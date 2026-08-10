# Görev 182 — İhtiyaç

SPEC 149 `archive --schema` genel archive şeması + SPEC 164
`sub_commands` alanı `restore` exit_codes=0/2/3/6 belgesi var.
Ama restore alt komutunun **payload biçimi ayrı JSON şeması yok** —
`--restore --json` dry-run çıktısı + `--restore --json-lines` NDJSON
kayıtları + SPEC 176 `--alert-webhook` payload'ı ayrı ayrı belge
gerektirir (SPEC 179 metrics --alert-history-show --schema kalıbı).

## Kabul

- `atlas archive --restore --schema [--pretty]`.
- SPEC 040/136/146/149/153/154/179 kalıbı — kısa devre; TASK_ID
  ve arşiv gerekmez; JSON şema tanımı basar.
- SPEC 149 `archive --schema` normal ile ÇAKIŞMAZ — `--restore`
  bayrağı verildi ve `--schema` de verildi ise SPEC 182 dalına düşer
  (SPEC 179 `metrics --alert-history-show --schema` dallanma kalıbı).
- JSON alanları:
  - `schema_version` = "1"
  - `dry_run_json_fields` (SPEC 127 `--restore --json` dry-run çıktısı):
    - `mode` (str "dry-run"), `task_id`, `archive`, `target`,
      `conflict` (bool)
  - `apply_json_fields` (SPEC 127 `--restore --json --apply` çıktısı):
    - `mode` (str "apply"), `task_id`, `archive`, `target`, `restored`
  - `jsonl_record_types` (SPEC 133 `--restore --json-lines`):
    - `plan` (task_id, archive, target, conflict)
    - `restored` (task_id, target, archive) — yalnız --apply
    - `summary` (task_id, mode, restored?)
  - `alert_payload_fields` (SPEC 176 `--restore --alert-webhook`):
    - `alert` (str "archive-restore"), `task_id` (str|null),
      `search_pattern` (str|null), `archive_root` (str),
      `error` (str), `exit_code` (int 2|3|6)
  - `exit_codes`: 0/2/3/6 (SPEC 033/071/176).
  - `notes`: SPEC 033/065/071/127/133/138/176/182 referansları.
- Parser DEĞİŞMEDİ (--schema + --pretty zaten SPEC 149'dan).
- `archive --restore --schema` mevcut `archive --schema` ile ÇAKIŞMAZ
  (--restore önce test; --schema önce yönlendirir).
- `--pretty` indent=2.

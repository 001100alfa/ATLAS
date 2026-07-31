# Görev 041.1 — Teslim

`atlas vault backup --auto` + `--keep N` — cron/scheduled retention.

## Uygulama

- `atlas_core/memory/vault_backup.py`
  - **Yeni fonksiyon**: `prune_backups(archive_root: Path, keep: int)
    -> list[Path]`
    - `keep < 1` → `VaultBackupError`.
    - `archive_root` yok → `[]` (cron nazikliği).
    - Sadece `vault-*.tar.gz` desenine dokunur.
    - Silme hatası → `VaultBackupError`.
- `atlas_core/cli.py::_cmd_vault_backup`
  - `--auto` + `--out` çakışma denetimi (exit 2).
  - `--keep < 1` denetimi (exit 2).
  - `--auto` → audit action = `backup-auto` (aksi hâlde `backup`).
  - Backup sonrası: `--keep` verilmişse ve `--out` yoksa
    `prune_backups` çağrılır; her silme audit'e `prune` olarak yazılır.
  - `--out` + `--keep` → stderr `UYARI` + retention atlanır (backup
    yine başarılı, exit 0).
- `atlas_core/cli.py` parser: `--auto` ve `--keep` bayrakları eklendi.

## Kanıtlar

- Birim testler (5): keep=1 en yeniyi tutar / keep ≥ toplam siler yok /
  desen dışı dosyaları korur / keep=0 hata / archive yok → boş liste.
- CLI testler (5): --auto default yol + audit=backup-auto / --auto+--out
  çakışma exit 2 / 3 dosya + backup + --keep 2 → 2 kalır + 2 prune
  audit / --out + --keep → UYARI + retention atlanır / --keep 0 exit 2.
- **+10 test** → tests/test_cli_vault_backup.py 14 → 24; toplam 773
  → **783 yeşil, 12 skip, cov %90.69**.
- `uv run mypy src` temiz; `uv run ruff check src tests` temiz;
  `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Yeni audit action'ları: `backup-auto`, `prune`, `prune-error`.
- Yeni bayraklar: `atlas vault backup --auto`, `atlas vault backup --keep N`.

## Değişmeyen sözleşme

- `atlas vault backup [--out]` bit-uyumlu (yeni bayraklar opsiyonel).
- `atlas vault restore` dokunulmadı.
- Exit kodları: sınıf aynı (2 = SPEC HATASI, 6 = backup/prune hata).
- `Vault` API dokunulmadı.

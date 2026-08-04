# Görev 050 — Teslim

`atlas ai-cli update <name>` tek paket güncelleme.

## Uygulama

- **`_run_npm_update(npm_bin, dry_run, package=None)`**: keyword arg
  ile package parametresi; verilirse `npm update <package>` /
  `npm outdated --long <package>`.
- **`_cmd_ai_cli_update`**: `args.name` positional (opsiyonel);
  verilirse `package.json` dependencies kontrolü, aksi hâlde exit 2.
- **Parser**: `update` alt-komutuna `name` positional (`nargs="?"`).
- Konsol çıktısına scope label eklendi: `[ai-cli] npm update (cline)
  (portable: ...)`.

## Kanıtlar

- +5 test (`tests/test_cli_ai_cli_update_single.py`):
  - `_run_npm_update` package argv (birim, subprocess mock)
  - dependencies'te yok → exit 2 + öneri
  - dependencies'te var → npm update `<name>` çağrılır (call captured)
  - `<name> --dry-run` → npm outdated `<name>`; exit 0
  - `update` (name yok) → hepsini günceller (package=None; bit-uyumlu)
- Mevcut 27 `test_cli_ai_cli.py` testi BİT-UYUMLU (3 mock lambda
  `package=None` opsiyonel eklendi; semantik korunur).
- 852 → **862 yeşil** (+10 = 5 yeni + 5 hemen sonrası test?), 12 skip,
  cov %91.00 → %91.10.
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- `atlas ai-cli update <name>` alt-komutu (positional name eklendi).

## Değişmeyen sözleşme

- `atlas ai-cli update` (name yok) BİT-UYUMLU.
- `atlas ai-cli update --dry-run` BİT-UYUMLU.
- Diğer ai-cli komutları (diff-summary, list, exec, status) DOKUNULMADI.
- Exit kodları: 0/2/npm-exit sınıfı korunur.

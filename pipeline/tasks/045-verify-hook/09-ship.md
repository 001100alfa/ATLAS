# Görev 045 — Teslim

SPEC 042 `vault verify --strict` pre-commit hook zincirine gate olarak.

## Uygulama

- `tools/hooks/pre-commit`: v2 → v3 yükseltme.
  - İmza satırı: `# atlas-hook v3`.
  - Doctor gate KORUNDU (`atlas doctor --strict --scan-src`).
  - Yeni gate:
    ```sh
    if [ -d vault ]; then
        if ! atlas vault verify --strict; then
            echo "..." >&2
            exit 1
        fi
    fi
    ```
- `src/atlas_core/cli.py::_HOOK_SIGNATURE` = `"# atlas-hook v3"`.
- `_is_atlas_hook` versiyon bilinçsiz (bit-uyumlu — v1/v2/v3 hepsi
  ATLAS shim'i sayılır; mevcut davranış).

## Kanıtlar

- +5 test (tests/test_cli_hooks.py `test_045_*`):
  - `_HOOK_SIGNATURE == "# atlas-hook v3"` sabit kontrolü
  - Şablon 2. satır `# atlas-hook v3` imzası
  - Şablon `atlas vault verify --strict` çağrısını içerir
  - `[ -d vault ]` guard verify'den ÖNCE
  - Doctor gate v3'te korundu (doctor önce, verify sonra)
- Mevcut **24 hook testi bit-uyumlu** yeşil.
- 822 → **827 yeşil**, 12 skip, cov %90.89.
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Pre-commit hook'ta vault graf sağlığı gate'i:
  - vault/ var + `verify --strict` bulgusu → commit ENGELLENIR (exit 1).
  - vault/ yok → gate atlanır (fresh clone naziksiz olmasın).
- Kurulu v2 hook'lar için `atlas hooks status` `target_up_to_date=False`;
  `atlas hooks install --force` ile v3'e geçilir.

## Değişmeyen sözleşme

- `atlas hooks {install,uninstall,status}` bit-uyumlu.
- SPEC 034 doctor gate zinciri korundu.
- `atlas vault verify` mevcut çıktıları bit-uyumlu (SPEC 042).

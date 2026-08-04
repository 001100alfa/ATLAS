# Görev 052 — Teslim

Vault verify auto-dump markdown raporu + hook v3 → v4.

## Uygulama

- **`atlas_core/memory/vault_verify.py`**:
  - Yeni fonksiyon: `format_report_markdown(report, vault_root) -> str`
    - Başlık + UTC timestamp + sayaçlar + durum satırı.
    - Koşullu 3 bölüm (kırık linkler / orfan notlar / orfan taglar).
    - Öneri bölümü yalnız bulgu varsa.
    - Deterministik sıralama (rapor zaten sıralı; format sırayı korur).
    - UTF-8 (Türkçe not adları/tag'ler bozulmadan).
- **`atlas_core/cli.py::_cmd_vault_verify`**:
  - Yeni argüman: `--dump-report PATH`.
  - Yazma sonrası `mkdir -p parents`; OSError sessiz.
  - Verify çıktısı bit-uyumlu (dump yan etki).
- **`tools/hooks/pre-commit`**:
  - v3 → v4 imza.
  - Verify çağrısı: `atlas vault verify --strict --dump-report
    .atlas/vault-health.md`.
  - Fail durumunda stderr'de "Detay rapor:" satırı.
- **`_HOOK_SIGNATURE`**: `v3 → v4`.

## Kanıtlar

- +9 test (`tests/test_cli_vault_verify_dump.py`):
  - **Birim (4)**: temiz vault + `Öneri` YOK / bulgulu vault + tüm
    bölümler / deterministik sıralama / UTF-8 karakterler
  - **CLI (5)**: dosya yazılır + stdout etkilenmez / dizin yoksa
    oluşturulur / `--strict + dump` → exit 4 KORUR / yazma hatası
    sessiz / `--json + --dump-report` ortogonal
- +1 test (`tests/test_cli_hooks.py::test_052_hook_sablonu_dump_report_bayragi_iceriyor`)
- **Mevcut testler bit-uyumlu**:
  - `test_cli_vault_verify.py` 14 test yeşil
  - `test_cli_hooks.py` 29 test (v3 → v4 imza güncellendi, mantık aynı)
- 842 → **852 yeşil**, 12 skip, cov %90.91 → %91.00.
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- `atlas vault verify --dump-report PATH` bayrağı.
- Pre-commit hook v4: fail durumunda `.atlas/vault-health.md`
  otomatik yazılır.

## Değişmeyen sözleşme

- `atlas vault verify [--json|--pretty|--strict]` bit-uyumlu (stdout
  + exit kodu).
- `atlas hooks {install,uninstall,status}` bit-uyumlu.
- Kurulu v3 hook'lar `hooks status`'ta `target_up_to_date=False`;
  kullanıcı `hooks install --force` ile v4'e geçer.

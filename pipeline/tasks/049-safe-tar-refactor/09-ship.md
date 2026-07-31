# Görev 049 — Teslim

SPEC 033 + SPEC 041 ortak tar üyesi güvenlik doğrulaması yardımcıya.

## Uygulama

- **Yeni namespace:** `src/atlas_core/utils/` (yeni top-level dizin;
  gelecek low-level yardımcılar için).
- **Yeni modül:** `src/atlas_core/utils/safe_tar.py`
  - `UnsafeTarMemberError(ValueError)` — N818 uyumlu.
  - `verify_tar_members(members: Iterable[TarInfo], expected_root: str)
    -> None` — 3 kontrol (traversal + kolon + kök); backslash normalize.
- `memory/archive.py::restore_task`:
  - 20 satır for loop → 4 satır `try/except UnsafeTarMemberError:
    raise RestoreError(str(exc)) from exc`.
  - `filter="data"` çağrısı KORUNDU.
- `memory/vault_backup.py::restore_vault`: aynı kalıp;
  `VaultBackupError` re-raise.

## Kanıtlar

- +12 birim test (tests/test_utils_safe_tar.py):
  - Mutlu yol: temiz üyeler, boş liste
  - Traversal: 4 varyant (bosluklu, başlangıç, mutlak, backslash)
  - Kolon: 2 varyant (NTFS ADS, drive letter)
  - Kök: 2 varyant (farklı, task_id)
  - Gerçek tar üzerinden getmembers() entegrasyonu
  - Mesaj sözleşmesi regex bit-uyumluluk kontrolü
- **Mevcut testler BİT-UYUMLU:**
  - `tests/test_cli_vault_backup.py` — 24 test yeşil.
  - `tests/test_cli_archive_restore.py` — 12 test yeşil.
  - Hiçbir mesaj regex'i güncellenmedi.
- Toplam: 810 → **822 yeşil, 12 skip, cov %90.87** (+12 test, +2 satır cov).
- `uv run mypy src` temiz (28 kaynak dosya, önceki 27 + safe_tar).
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- **YOK** — refactor. Public API dokunulmadı; davranış bit-uyumlu.

## Değişmeyen sözleşme

- `RestoreError`, `VaultBackupError` public hâlâ; mesaj metinleri korundu.
- `atlas archive --restore` bit-uyumlu.
- `atlas vault restore` bit-uyumlu.
- `filter="data"` extract güvenliği KORUNDU (ikinci kat defense).

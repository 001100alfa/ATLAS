# Görev 049 — İhtiyaç

SPEC 033 (`memory/archive.py::restore_task`, 148 satır) ve SPEC 041
(`memory/vault_backup.py::restore_vault`, 92 satır) aynı 3 güvenlik
kontrolünü tekrarlıyor: path traversal (`..` + mutlak yol), Windows
kolon (NTFS ADS), beklenen kök arcname. Kalıp DECISIONS 2026-07-30
notunda "gelecekte ortak yardımcıya çıkarılabilir" olarak flag'lenmiş.

Şu an duplike kod → bakım maliyeti + gelecekte üçüncü tar-tabanlı
komut (backup formatını değiştiren, ör. `hooks export`) eklerken üç
noktada aynı hata riskini taşır.

## Kabul kriteri

- Yeni modül: `src/atlas_core/utils/safe_tar.py`
  - `class UnsafeTarMemberError(ValueError)` — N818 uyumlu.
  - `verify_tar_members(members, expected_root: str) -> None`
    - Her üye için 3 kontrol; ihlalde `UnsafeTarMemberError`.
    - **Mesaj metni** SPEC 033/041 sözleşmesini KORUR:
      - `"güvensiz üye adı (path traversal?): <name>"`
      - `"güvensiz üye adı (kolon): <name>"`
      - `"beklenmeyen kök: '<got>' (bekleniyor: '<expected>')"`
    - Backslash normalize edilir (`\` → `/`).
- `memory/archive.py::restore_task`:
  - For loop kaldırılır → `verify_tar_members(members, task_id)` +
    `try/except UnsafeTarMemberError as exc: raise RestoreError(str(exc)) from exc`.
  - `tar.extractall(..., filter="data")` çağrısı KORUNUR (ortogonal
    defense-in-depth).
- `memory/vault_backup.py::restore_vault`: aynı kalıp, `VaultBackupError`.
- **Mevcut testler (bit-uyumlu):**
  - `tests/test_cli_archive_restore.py` — SPEC 033 restore.
  - `tests/test_cli_vault_backup.py` — SPEC 041 restore.
  - Her ikisi de mesaj regex'iyle kontrol ediyor; hiçbiri değiştirilmez.
- Yeni +12 birim test (traversal 4 varyant, kolon 2, kök 2, mutlu 2,
  gerçek tar 1, mesaj sözleşmesi 1).

## Riskli

- Testler `match=r"güvensiz"` gibi regex kullanıyor. `str(exc)` ile
  re-raise ederken tam metin korunmalı — `verify_tar_members` mesajları
  birebir SPEC 033/041 kalıbı olacak.
- `UnsafeTarMemberError` `ValueError` alt-tipi (domain-agnostik).
  Çağıran taraf tam metni koruyarak kendi domain hatasına sarar.
- Ek modül `atlas_core/utils/` yeni bir top-level namespace açıyor;
  gelecekte başka low-level yardımcılar için hazır. Boş `__init__.py`
  ile içi belirlenmemiş — YAGNI.

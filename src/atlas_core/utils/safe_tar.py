"""SPEC 049: Ortak tar üyesi güvenlik doğrulaması.

SPEC 033 (`memory/archive.py::restore_task`) ve SPEC 041
(`memory/vault_backup.py::restore_vault`) aynı 4 kontrolü yapıyordu:

1. Path traversal (`..` bileşeni veya mutlak yol `/foo` başlangıcı)
2. Windows kolon (`:` — NTFS Alternate Data Stream açığı)
3. Beklenen kök arcname (tar üyesinin ilk yol bileşeni sabit)
4. `filter="data"` ile ekstra güvenlik (çağıran tarafta uygulanır)

Bu modül 1-3 kontrollerini tek fonksiyonda toplar; her iki çağıran
`UnsafeTarMemberError` yakalayıp kendi domain hatasına dönüştürür
(mesaj metnini korumak zorunda — mevcut testler regex ile kontrol
ediyor).

`filter="data"` çağıran tarafta kalır çünkü ekstra üye-üye kontrol
değil, `tarfile.extractall()` çağrısının argümanı.
"""

from __future__ import annotations

from collections.abc import Iterable
from tarfile import TarInfo


class UnsafeTarMemberError(ValueError):
    """SPEC 049: Tar üyesi güvenlik ihlali (traversal/kolon/kök).

    Domain-agnostik ValueError alt-tipi — çağıran taraf kendi domain
    hatasına (RestoreError, VaultBackupError) sarar. Ruff N818: 'Error'
    sonekli.
    """


def verify_tar_members(
    members: Iterable[TarInfo], expected_root: str,
) -> None:
    """SPEC 049: Tar üyelerini güvenlik açısından doğrula.

    Args:
        members: `tarfile.TarFile.getmembers()` çıktısı (veya iter).
        expected_root: Tar içinde beklenen ilk yol bileşeni (arcname
            kökü). Her üyenin `name.split('/', 1)[0]` bu değere eşit
            olmalı. Örn `"vault"` (SPEC 041) veya `task_id` (SPEC 033).

    Raises:
        UnsafeTarMemberError: 3 kontrolden herhangi biri başarısız ise.
            Mesaj metni mevcut SPEC 033/041 sözleşmesini korur:
              - "güvensiz üye adı (path traversal?): <name>"
              - "güvensiz üye adı (kolon): <name>"
              - "beklenmeyen kök: '<got>' (bekleniyor: '<expected>')"

    Not:
        Bu fonksiyon `filter="data"` DEĞİL — o `extractall()`
        argümanıdır. İki kontrol ortogonal ve birbirini destekler
        (defense-in-depth).
    """
    for m in members:
        # Windows backslash → forward slash (Python tar hep '/' bekler)
        name = m.name.replace("\\", "/")
        if name.startswith("/") or ".." in name.split("/"):
            raise UnsafeTarMemberError(
                f"güvensiz üye adı (path traversal?): {m.name}"
            )
        if ":" in name:
            raise UnsafeTarMemberError(
                f"güvensiz üye adı (kolon): {m.name}"
            )
        first = name.split("/", 1)[0]
        if first != expected_root:
            raise UnsafeTarMemberError(
                f"beklenmeyen kök: '{first}' "
                f"(bekleniyor: '{expected_root}')"
            )

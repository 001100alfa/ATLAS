"""SPEC 049 — ortak tar üyesi güvenlik doğrulaması (verify_tar_members)."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from atlas_core.utils.safe_tar import UnsafeTarMemberError, verify_tar_members


def _mk_member(name: str, size: int = 0) -> tarfile.TarInfo:
    """Yardımcı: `TarInfo` üretir (dosya sistemi dokunulmaz)."""
    info = tarfile.TarInfo(name=name)
    info.size = size
    return info


# ═════════════════════════════════════════════════════════════════════
# Mutlu yol
# ═════════════════════════════════════════════════════════════════════


def test_049_temiz_uyeler_gecer() -> None:
    """Kök doğru + traversal/kolon yok → istisna atmadan döner."""
    members = [
        _mk_member("vault/notes/a.md"),
        _mk_member("vault/daily/2026-07-31.md"),
        _mk_member("vault"),  # dizin kaydı — ilk bileşen kendisi
    ]
    verify_tar_members(members, expected_root="vault")


def test_049_bos_uye_listesi_hata_atmaz() -> None:
    """Boş iterable → istisna yok (nazik davranış)."""
    verify_tar_members([], expected_root="vault")


# ═════════════════════════════════════════════════════════════════════
# Path traversal
# ═════════════════════════════════════════════════════════════════════


def test_049_traversal_bosluklu_dotdot_reddedilir() -> None:
    with pytest.raises(UnsafeTarMemberError, match="path traversal"):
        verify_tar_members(
            [_mk_member("vault/../evil.txt")],
            expected_root="vault",
        )


def test_049_traversal_baslangicta_dotdot_reddedilir() -> None:
    with pytest.raises(UnsafeTarMemberError, match="path traversal"):
        verify_tar_members(
            [_mk_member("../evil.txt")],
            expected_root="vault",
        )


def test_049_mutlak_yol_reddedilir() -> None:
    with pytest.raises(UnsafeTarMemberError, match="path traversal"):
        verify_tar_members(
            [_mk_member("/etc/passwd")],
            expected_root="vault",
        )


def test_049_backslash_traversal_da_reddedilir() -> None:
    """Windows-stil `..\\evil` → normalize edilir + reddedilir."""
    with pytest.raises(UnsafeTarMemberError, match="path traversal"):
        verify_tar_members(
            [_mk_member("vault\\..\\evil.txt")],
            expected_root="vault",
        )


# ═════════════════════════════════════════════════════════════════════
# Windows kolon (NTFS ADS)
# ═════════════════════════════════════════════════════════════════════


def test_049_kolon_reddedilir() -> None:
    with pytest.raises(UnsafeTarMemberError, match="kolon"):
        verify_tar_members(
            [_mk_member("vault/notes/a.md:evil")],
            expected_root="vault",
        )


def test_049_windows_drive_letter_kolon_reddedilir() -> None:
    """`C:vault/x.md` → kolon var, reddedilir."""
    with pytest.raises(UnsafeTarMemberError, match="kolon"):
        verify_tar_members(
            [_mk_member("C:vault/x.md")],
            expected_root="vault",
        )


# ═════════════════════════════════════════════════════════════════════
# Beklenmeyen kök
# ═════════════════════════════════════════════════════════════════════


def test_049_beklenmeyen_kok_reddedilir() -> None:
    with pytest.raises(UnsafeTarMemberError, match="beklenmeyen kök"):
        verify_tar_members(
            [_mk_member("baska/x.md")],
            expected_root="vault",
        )


def test_049_kok_task_id_beklentisi() -> None:
    """SPEC 033 kalıbı: expected_root task_id ise farklı kök hata."""
    with pytest.raises(UnsafeTarMemberError, match="beklenmeyen kök"):
        verify_tar_members(
            [_mk_member("task-042/00-need.md")],
            expected_root="task-041",
        )


# ═════════════════════════════════════════════════════════════════════
# Entegrasyon: gerçek tar üzerinde
# ═════════════════════════════════════════════════════════════════════


def test_049_gercek_tar_uyeleri_ile(tmp_path: Path) -> None:
    """Gerçek `.tar.gz` üretilip `getmembers()` ile doğrulanır."""
    src = tmp_path / "vault"
    src.mkdir()
    (src / "a.md").write_text("ok", encoding="utf-8")
    tar_path = tmp_path / "b.tar.gz"
    with tarfile.open(tar_path, "w:gz") as t:
        t.add(src, arcname="vault")

    with tarfile.open(tar_path, "r:gz") as t:
        verify_tar_members(t.getmembers(), expected_root="vault")


def test_049_hata_mesaj_sozlesmesi_sabit() -> None:
    """SPEC 033/041 mesaj sözleşmesi — regex'ler bit-uyumlu kalmalı."""
    with pytest.raises(
        UnsafeTarMemberError,
        match=r"güvensiz üye adı \(path traversal\?\): \.\./evil",
    ):
        verify_tar_members([_mk_member("../evil")], expected_root="vault")

    with pytest.raises(
        UnsafeTarMemberError,
        match=r"güvensiz üye adı \(kolon\): vault/a:b",
    ):
        verify_tar_members([_mk_member("vault/a:b")], expected_root="vault")

    with pytest.raises(
        UnsafeTarMemberError,
        match=r"beklenmeyen kök: 'baska' \(bekleniyor: 'vault'\)",
    ):
        verify_tar_members([_mk_member("baska/x")], expected_root="vault")

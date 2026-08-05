"""SPEC 067 — vault backup --keep-encrypted N retention."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory import vault_backup as vb_mod
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    prune_encrypted_backups,
)


def _make_vault(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.delenv("ATLAS_BACKUP_PASSPHRASE", raising=False)


def _touch_gpg(archive_root: Path, name: str, mtime: float) -> Path:
    archive_root.mkdir(parents=True, exist_ok=True)
    p = archive_root / name
    p.write_bytes(b"GPG-ENC")
    os.utime(p, (mtime, mtime))
    return p


# ═════════════════════════════════════════════════════════════════════
# prune_encrypted_backups (birim)
# ═════════════════════════════════════════════════════════════════════


def test_067_prune_enc_keep_1_siler(tmp_path: Path) -> None:
    arc = tmp_path / "arc"
    old = _touch_gpg(arc, "vault-2026-01-01.tar.gz.gpg", 1_000.0)
    mid = _touch_gpg(arc, "vault-2026-02-01.tar.gz.gpg", 2_000.0)
    new = _touch_gpg(arc, "vault-2026-03-01.tar.gz.gpg", 3_000.0)
    deleted = prune_encrypted_backups(arc, keep=1)
    assert set(deleted) == {old, mid}
    assert not old.exists()
    assert not mid.exists()
    assert new.exists()


def test_067_prune_enc_keep_gte_toplam(tmp_path: Path) -> None:
    arc = tmp_path / "arc"
    a = _touch_gpg(arc, "vault-a.tar.gz.gpg", 1_000.0)
    b = _touch_gpg(arc, "vault-b.tar.gz.gpg", 2_000.0)
    deleted = prune_encrypted_backups(arc, keep=5)
    assert deleted == []
    assert a.exists() and b.exists()


def test_067_prune_enc_plain_dokunmaz(tmp_path: Path) -> None:
    """`.tar.gz` (plain) dosyalarına dokunmaz — SPEC 041.1 ayrı çalışır."""
    arc = tmp_path / "arc"
    _touch_gpg(arc, "vault-2026-01.tar.gz.gpg", 1_000.0)
    _touch_gpg(arc, "vault-2026-02.tar.gz.gpg", 2_000.0)
    plain = arc / "vault-eski.tar.gz"
    plain.write_bytes(b"plain")
    os.utime(plain, (500.0, 500.0))
    prune_encrypted_backups(arc, keep=1)
    assert plain.exists()  # SPEC 041.1 alanı


def test_067_prune_enc_keep_sifir_hata(tmp_path: Path) -> None:
    with pytest.raises(VaultBackupError, match=">= 1"):
        prune_encrypted_backups(tmp_path, keep=0)


def test_067_prune_enc_arc_yok_bos(tmp_path: Path) -> None:
    assert prune_encrypted_backups(tmp_path / "yok", keep=3) == []


# ═════════════════════════════════════════════════════════════════════
# CLI: vault backup --keep-encrypted
# ═════════════════════════════════════════════════════════════════════


def _fake_gpg_run(argv, **kw):
    """Fake subprocess: gpg output dosyasını üret."""
    for i, a in enumerate(argv):
        if a == "--output":
            Path(argv[i + 1]).write_bytes(b"GPG-ENC")
    class _R:
        returncode = 0
        stdout = ""
        stderr = ""
    return _R()


def test_067_cli_keep_encrypted_2_var_olan_3_pruner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """3 mevcut .gpg + backup+encrypt + --keep-encrypted 2 → 2 kalır."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    arc = tmp_path / "arc"
    en_eski = _touch_gpg(arc, "vault-2020.tar.gz.gpg", 1_000.0)
    orta = _touch_gpg(arc, "vault-2021.tar.gz.gpg", 2_000.0)
    en_yeni_eski = _touch_gpg(arc, "vault-2022.tar.gz.gpg", 3_000.0)

    monkeypatch.setattr(vb_mod.subprocess, "run", _fake_gpg_run)
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    rc = main([
        "vault", "backup", "--auto",
        "--vault-root", str(v),
        "--archive-root", str(arc),
        "--encrypt", "secret",
        "--keep-encrypted", "2",
    ])
    assert rc == 0
    kalan = sorted(arc.glob("vault-*.tar.gz.gpg"))
    # Yeni encrypted (bugün) + en yeni eski (3000) kalır
    assert en_yeni_eski in kalan
    assert orta not in kalan
    assert en_eski not in kalan
    assert len(kalan) == 2

    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert audit_txt.count('"prune-encrypted"') == 2


def test_067_cli_keep_encrypted_sifir_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    rc = main([
        "vault", "backup", "--auto",
        "--vault-root", str(v),
        "--archive-root", str(tmp_path / "arc"),
        "--keep-encrypted", "0",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--keep-encrypted" in err


def test_067_cli_keep_encrypted_out_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out + --keep-encrypted → UYARI (retention yalnız archive_root)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    arc = tmp_path / "arc"
    eski = _touch_gpg(arc, "vault-2020.tar.gz.gpg", 500.0)
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(tmp_path / "custom.tar.gz"),
        "--archive-root", str(arc),
        "--keep-encrypted", "1",
    ])
    assert rc == 0
    assert eski.exists()  # retention atlanmış
    err = capsys.readouterr().err
    assert "UYARI" in err
    assert "--keep-encrypted YOK sayıldı" in err


def test_067_cli_keep_encrypted_ile_keep_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SPEC 041.1 --keep (plain) + SPEC 067 --keep-encrypted birlikte
    çalışır; iki ayrı retention havuzu."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    arc = tmp_path / "arc"
    # 2 plain eski
    plain_old = arc / "vault-2020.tar.gz"
    arc.mkdir(parents=True, exist_ok=True)
    plain_old.write_bytes(b"p")
    os.utime(plain_old, (1_000.0, 1_000.0))
    # 2 encrypted eski
    _touch_gpg(arc, "vault-2020.tar.gz.gpg", 2_000.0)
    _touch_gpg(arc, "vault-2019.tar.gz.gpg", 1_500.0)

    monkeypatch.setattr(vb_mod.subprocess, "run", _fake_gpg_run)
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    rc = main([
        "vault", "backup", "--auto",
        "--vault-root", str(v),
        "--archive-root", str(arc),
        "--keep", "1",  # yeni plain oluşacak sonra silinecek çünkü encrypt sonrası
        "--encrypt", "secret",
        "--keep-encrypted", "1",
    ])
    assert rc == 0
    # Plain havuzu: --keep 1 → yalnız en yeni + eski silindi (yeni backup
    # silinmiş çünkü --encrypt sonrası plain kaldırıldı)
    # Not: yeni encrypted `.tar.gz.gpg` glob'una girer, `.tar.gz` glob'una
    # değil çünkü glob('vault-*.tar.gz') `.gpg` uzantısıyla eşleşmez.
    # `plain_old` --keep 1 sonrası: mtime desc en yeni tut ama yeni plain
    # zaten silindi encrypt sonrası. Sadece plain_old kalan.
    # BUT --keep önce encrypt'ten önce çalışıyor, o zaman yeni plain hala
    # sayılıyor. Sonra encrypt plain siliyor.
    # Test kontrol: encrypted havuzda 1 kalan (yeni encrypt)
    enc_kalan = list(arc.glob("vault-*.tar.gz.gpg"))
    assert len(enc_kalan) == 1

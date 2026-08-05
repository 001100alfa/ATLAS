"""SPEC 102 — atlas vault restore <first.001> --split testleri."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    combine_split_parts,
    split_backup,
)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "target-vault"))
    monkeypatch.chdir(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# hello", encoding="utf-8")
    return vault


def _make_backup(vault: Path, archive_root: Path) -> Path:
    """Basit vault yedeği üret ve döner."""
    archive_root.mkdir(parents=True, exist_ok=True)
    out = archive_root / "vault-backup.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        tar.add(vault, arcname="vault")
    return out


# ═════════════════════════════════════════════════════════════════════
# combine_split_parts birim
# ═════════════════════════════════════════════════════════════════════


def test_102_combine_temel(tmp_path: Path) -> None:
    """3 parçadan birleştirme → orijinal veri."""
    src = tmp_path / "data.bin"
    original = b"abcdefghij" * (256 * 1024)  # ~2.5 MB
    src.write_bytes(original)
    parts = split_backup(src, 1)
    assert len(parts) == 3
    combined = combine_split_parts(parts[0])
    assert combined.read_bytes() == original
    # Parçalar korundu (silinmedi)
    for p in parts:
        assert p.is_file()


def test_102_combine_yanlis_uzanti(tmp_path: Path) -> None:
    """Path `.001` uzantısız → VaultBackupError."""
    src = tmp_path / "data.txt"
    src.write_bytes(b"x")
    with pytest.raises(VaultBackupError, match="'.001' olmalı"):
        combine_split_parts(src)


def test_102_combine_ilk_parca_yok(tmp_path: Path) -> None:
    src = tmp_path / "yok.tar.gz.001"
    with pytest.raises(VaultBackupError, match="ilk parça yok"):
        combine_split_parts(src)


def test_102_combine_tek_parca(tmp_path: Path) -> None:
    """Tek parça (küçük dosya) → tam kopya."""
    src = tmp_path / "small.bin"
    src.write_bytes(b"x" * 100)
    parts = split_backup(src, 10)
    assert len(parts) == 1
    combined = combine_split_parts(parts[0])
    assert combined.read_bytes() == b"x" * 100


# ═════════════════════════════════════════════════════════════════════
# CLI --split restore
# ═════════════════════════════════════════════════════════════════════


def test_102_restore_split_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Split parçalardan restore → hedef vault içerik doğru."""
    vault = _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    backup = _make_backup(vault, archive)
    parts = split_backup(backup, 1)
    # Hedef vault (env ATLAS_VAULT)
    target = tmp_path / "target-vault"
    rc = main([
        "vault", "restore", str(parts[0]),
        "--split", "--apply",
        "--vault-root", str(target),
    ])
    assert rc == 0
    assert (target / "note.md").read_text(encoding="utf-8") == "# hello"


def test_102_restore_split_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--split dry-run → birleştirme YAPILMAZ."""
    vault = _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    backup = _make_backup(vault, archive)
    parts = split_backup(backup, 1)
    target = tmp_path / "target-vault"
    rc = main([
        "vault", "restore", str(parts[0]), "--split",
        "--vault-root", str(target),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "split parça birleştir" in out


def test_102_restore_split_yanlis_uzanti(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`.001` değil → SPEC HATASI exit 2."""
    vault = _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    backup = _make_backup(vault, archive)
    rc = main([
        "vault", "restore", str(backup), "--split", "--apply",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert ".001" in err


def test_102_restore_split_decrypt_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--split + --decrypt → MUTEX exit 2."""
    vault = _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    backup = _make_backup(vault, archive)
    parts = split_backup(backup, 1)
    rc = main([
        "vault", "restore", str(parts[0]),
        "--split", "--decrypt", "secret", "--apply",
    ])
    assert rc == 2


def test_102_restore_split_decrypt_recipient_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--split + --decrypt-recipient → MUTEX exit 2."""
    vault = _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    backup = _make_backup(vault, archive)
    parts = split_backup(backup, 1)
    rc = main([
        "vault", "restore", str(parts[0]),
        "--split", "--decrypt-recipient", "--apply",
    ])
    assert rc == 2


def test_102_restore_split_parcalar_korundu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Restore sonrası split parçaları silinmez."""
    vault = _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    backup = _make_backup(vault, archive)
    parts = split_backup(backup, 1)
    target = tmp_path / "target-vault"
    rc = main([
        "vault", "restore", str(parts[0]),
        "--split", "--apply",
        "--vault-root", str(target),
    ])
    assert rc == 0
    for p in parts:
        assert p.is_file()


def test_102_restore_split_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--split YOK → SPEC 041 normal restore AYNI."""
    vault = _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    backup = _make_backup(vault, archive)
    target = tmp_path / "target-vault"
    rc = main([
        "vault", "restore", str(backup), "--apply",
        "--vault-root", str(target),
    ])
    assert rc == 0
    assert (target / "note.md").read_text(encoding="utf-8") == "# hello"

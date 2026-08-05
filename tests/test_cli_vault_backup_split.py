"""SPEC 101 — atlas vault backup --split SIZE_MB testleri."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault_backup import VaultBackupError, split_backup


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "vault"))
    monkeypatch.chdir(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# test", encoding="utf-8")
    return vault


# ═════════════════════════════════════════════════════════════════════
# split_backup birim
# ═════════════════════════════════════════════════════════════════════


def test_101_split_kucuk_dosya_tek_parca(tmp_path: Path) -> None:
    """1 KB dosya + 1 MB split → tek parça .001."""
    src = tmp_path / "data.bin"
    src.write_bytes(b"x" * 1024)
    parts = split_backup(src, 1)
    assert len(parts) == 1
    assert parts[0].name == "data.bin.001"
    assert parts[0].read_bytes() == b"x" * 1024
    assert not src.exists()  # orijinal silindi


def test_101_split_buyuk_dosya_coklu_parca(tmp_path: Path) -> None:
    """3 MB dosya + 1 MB split → 3 parça."""
    src = tmp_path / "data.bin"
    src.write_bytes(b"a" * (3 * 1024 * 1024))
    parts = split_backup(src, 1)
    assert len(parts) == 3
    for i, p in enumerate(parts, start=1):
        assert p.name == f"data.bin.{i:03d}"
        assert len(p.read_bytes()) == 1024 * 1024
    # Toplam birleştirilmiş içerik
    joined = b"".join(p.read_bytes() for p in parts)
    assert joined == b"a" * (3 * 1024 * 1024)


def test_101_split_size_mb_gecersiz(tmp_path: Path) -> None:
    src = tmp_path / "data.bin"
    src.write_bytes(b"x")
    with pytest.raises(VaultBackupError, match="size_mb"):
        split_backup(src, 0)
    with pytest.raises(VaultBackupError, match="size_mb"):
        split_backup(src, -5)


def test_101_split_src_yok(tmp_path: Path) -> None:
    src = tmp_path / "yok.bin"
    with pytest.raises(VaultBackupError, match="kaynak yok"):
        split_backup(src, 1)


# ═════════════════════════════════════════════════════════════════════
# CLI --split
# ═════════════════════════════════════════════════════════════════════


def test_101_cli_split_kucuk_vault(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Küçük vault + 1 MB split → tek parça .001, orijinal silindi."""
    _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    rc = main([
        "vault", "backup",
        "--archive-root", str(archive),
        "--split", "1",
    ])
    assert rc == 0
    tars = list(archive.glob("vault-*.tar.gz"))
    parts = list(archive.glob("vault-*.tar.gz.001"))
    assert len(tars) == 0  # orijinal silindi
    assert len(parts) == 1
    out = capsys.readouterr().out
    assert "1 parça" in out or "1 parçaya bölündü" in out


def test_101_cli_split_size_sifir_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    rc = main([
        "vault", "backup",
        "--archive-root", str(archive),
        "--split", "0",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--split" in err


def test_101_cli_split_encrypt_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--split + --encrypt → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    rc = main([
        "vault", "backup",
        "--archive-root", str(archive),
        "--split", "1", "--encrypt", "secret",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--split" in err
    assert "--encrypt" in err or "--recipient" in err


def test_101_cli_split_recipient_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    rc = main([
        "vault", "backup",
        "--archive-root", str(archive),
        "--split", "1", "--recipient", "KEY123",
    ])
    assert rc == 2


def test_101_cli_split_out_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--split + --out → PATH'e yazıp orada parçalanır."""
    _env(monkeypatch, tmp_path)
    out = tmp_path / "custom" / "backup.tar.gz"
    rc = main([
        "vault", "backup",
        "--out", str(out),
        "--split", "1",
    ])
    assert rc == 0
    assert not out.exists()  # orijinal silindi
    parts = list((tmp_path / "custom").glob("backup.tar.gz.*"))
    assert len(parts) >= 1


def test_101_cli_split_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--split YOK → SPEC 041 tek .tar.gz yazılır."""
    _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    rc = main([
        "vault", "backup",
        "--archive-root", str(archive),
    ])
    assert rc == 0
    tars = list(archive.glob("vault-*.tar.gz"))
    parts = list(archive.glob("vault-*.tar.gz.001"))
    assert len(tars) == 1
    assert len(parts) == 0  # split yok


def test_101_cli_split_retention_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--keep 1 --split → retention split'ten önce çalışır (parçalar
    dahil edilmez)."""
    _env(monkeypatch, tmp_path)
    archive = tmp_path / "arc"
    archive.mkdir()
    # 2 eski yedek ekle
    (archive / "vault-2024-01-01-0000.tar.gz").write_bytes(b"old1")
    (archive / "vault-2024-02-01-0000.tar.gz").write_bytes(b"old2")
    rc = main([
        "vault", "backup",
        "--archive-root", str(archive),
        "--keep", "1", "--split", "1",
    ])
    assert rc == 0
    # 1 yeni backup parçalı; 2 eski silindi
    remaining_tars = list(archive.glob("vault-*.tar.gz"))
    remaining_parts = list(archive.glob("vault-*.tar.gz.001"))
    assert len(remaining_tars) == 0  # yeni de parçalandı
    assert len(remaining_parts) == 1

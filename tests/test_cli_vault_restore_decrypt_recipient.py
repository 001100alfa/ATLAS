"""SPEC 078 — vault restore --decrypt-recipient asimetrik decrypt."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory import vault_backup as vb_mod
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    backup_vault,
    decrypt_backup_recipient,
)


def _make_vault(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.delenv("ATLAS_BACKUP_PASSPHRASE", raising=False)


# ═════════════════════════════════════════════════════════════════════
# decrypt_backup_recipient (birim, subprocess mock)
# ═════════════════════════════════════════════════════════════════════


def test_078_decrypt_recipient_kaynak_yok(tmp_path: Path) -> None:
    with pytest.raises(VaultBackupError, match="kaynak yok"):
        decrypt_backup_recipient(
            tmp_path / "yok.gpg",
            tmp_path / "out.tar.gz",
            gpg_bin="/fake/gpg",
        )


def test_078_decrypt_recipient_gpg_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    enc = tmp_path / "e.tar.gz.gpg"
    enc.write_bytes(b"ENC")
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: None)
    with pytest.raises(VaultBackupError, match="gpg bulunamadı"):
        decrypt_backup_recipient(enc, tmp_path / "out.tar.gz")


def test_078_decrypt_recipient_argv_passphrase_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """gpg --decrypt --output <out> <enc>; passphrase YOK (asimetrik)."""
    enc = tmp_path / "e.tar.gz.gpg"
    enc.write_bytes(b"ENC")
    out = tmp_path / "out.tar.gz"
    captured: dict = {}

    def fake_run(argv, **kw):
        captured["argv"] = list(argv)
        captured["input"] = kw.get("input")  # None olmalı
        Path(argv[argv.index("--output") + 1]).write_bytes(b"PLAIN")
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(vb_mod.subprocess, "run", fake_run)
    result = decrypt_backup_recipient(enc, out, gpg_bin="/fake/gpg")
    assert result == out
    argv = captured["argv"]
    assert argv[0] == "/fake/gpg"
    assert "--decrypt" in argv
    # Passphrase argv'de VE stdin'de YOK
    assert "--passphrase-fd" not in argv
    assert captured["input"] is None


def test_078_decrypt_recipient_exit_kod_hata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    enc = tmp_path / "e.tar.gz.gpg"
    enc.write_bytes(b"ENC")

    class _R:
        returncode = 2
        stdout = ""
        stderr = "gpg: no secret key\n"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _R())
    with pytest.raises(VaultBackupError, match="gpg decrypt hatası"):
        decrypt_backup_recipient(enc, tmp_path / "out.tar.gz",
                                 gpg_bin="/fake/gpg")


# ═════════════════════════════════════════════════════════════════════
# CLI: vault restore --decrypt-recipient
# ═════════════════════════════════════════════════════════════════════


def _make_backup_then_fake_encrypt(tmp_path: Path) -> Path:
    v = tmp_path / "src-vault"
    _make_vault(v, {"a.md": "orjinal-icerik"})
    plain = tmp_path / "b.tar.gz"
    backup_vault(v, plain)
    enc = tmp_path / "b.tar.gz.gpg"
    enc.write_bytes(plain.read_bytes())
    plain.unlink()
    return enc


def _fake_gpg_decrypt_identity(argv, **kw):
    """gpg mock: input dosyayı output'a kopyala (identity decrypt)."""
    inp = argv[-1]
    out = argv[argv.index("--output") + 1]
    Path(out).write_bytes(Path(inp).read_bytes())
    class _R:
        returncode = 0
        stdout = ""
        stderr = ""
    return _R()


def test_078_cli_restore_decrypt_recipient_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--decrypt-recipient + .tar.gz.gpg + --apply → asimetrik restore."""
    _env(monkeypatch, tmp_path)
    enc = _make_backup_then_fake_encrypt(tmp_path)
    monkeypatch.setattr(vb_mod.subprocess, "run", _fake_gpg_decrypt_identity)
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    target = tmp_path / "restored-vault"
    rc = main([
        "vault", "restore", str(enc),
        "--apply", "--decrypt-recipient",
        "--vault-root", str(target),
    ])
    assert rc == 0
    assert (target / "a.md").read_text(encoding="utf-8") == "orjinal-icerik"
    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "decrypt-recipient" in audit_txt
    assert "restore" in audit_txt
    # Temp plain silindi
    assert list(target.parent.glob(".vault-restore-decrypt-*.tar.gz")) == []


def test_078_cli_restore_decrypt_recipient_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dry-run → 'asimetrik decrypt (private key) → restore' mesajı."""
    _env(monkeypatch, tmp_path)
    enc = _make_backup_then_fake_encrypt(tmp_path)
    rc = main([
        "vault", "restore", str(enc), "--decrypt-recipient",
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "asimetrik" in out
    assert "SPEC 078" in out


def test_078_cli_restore_decrypt_ve_recipient_mutex_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    enc = _make_backup_then_fake_encrypt(tmp_path)
    rc = main([
        "vault", "restore", str(enc), "--apply",
        "--decrypt", "s", "--decrypt-recipient",
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--decrypt ve --decrypt-recipient" in err


def test_078_cli_restore_decrypt_recipient_gpg_hata_exit_6(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    enc = _make_backup_then_fake_encrypt(tmp_path)

    class _R:
        returncode = 2
        stdout = ""
        stderr = "gpg: no secret key"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _R())
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    rc = main([
        "vault", "restore", str(enc), "--apply", "--decrypt-recipient",
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "DECRYPT HATASI" in err


def test_078_cli_restore_gpg_uzanti_uyari_iki_moda_isaret(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """.gpg uzantı + iki decrypt de yok → UYARI iki moda işaret."""
    _env(monkeypatch, tmp_path)
    enc = _make_backup_then_fake_encrypt(tmp_path)
    rc = main([
        "vault", "restore", str(enc),
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 0
    err = capsys.readouterr().err
    assert "UYARI" in err
    assert "--decrypt/--decrypt-recipient" in err

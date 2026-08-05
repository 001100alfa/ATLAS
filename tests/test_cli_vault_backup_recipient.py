"""SPEC 073 — vault backup --recipient GPG public-key testleri."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory import vault_backup as vb_mod
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    encrypt_backup_recipient,
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
# encrypt_backup_recipient (birim, subprocess mock)
# ═════════════════════════════════════════════════════════════════════


def test_073_encrypt_recipient_kaynak_yok(tmp_path: Path) -> None:
    with pytest.raises(VaultBackupError, match="kaynak yok"):
        encrypt_backup_recipient(
            tmp_path / "yok.tar.gz",
            tmp_path / "out.gpg",
            recipient="user@example.com",
            gpg_bin="/fake/gpg",
        )


def test_073_encrypt_recipient_bos_hata(tmp_path: Path) -> None:
    plain = tmp_path / "p.tar.gz"
    plain.write_bytes(b"data")
    with pytest.raises(VaultBackupError, match="recipient .* boş"):
        encrypt_backup_recipient(plain, tmp_path / "out.gpg",
                                 recipient="", gpg_bin="/fake/gpg")


def test_073_encrypt_recipient_gpg_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    plain = tmp_path / "p.tar.gz"
    plain.write_bytes(b"data")
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: None)
    with pytest.raises(VaultBackupError, match="gpg bulunamadı"):
        encrypt_backup_recipient(plain, tmp_path / "out.gpg",
                                 recipient="user@x")


def test_073_encrypt_recipient_argv_dogru(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """gpg --encrypt --recipient <KEY> --trust-model always ...
    Passphrase YOK (asimetrik)."""
    plain = tmp_path / "p.tar.gz"
    plain.write_bytes(b"data")
    out = tmp_path / "out.tar.gz.gpg"
    captured: dict = {}

    def fake_run(argv, **kw):
        captured["argv"] = list(argv)
        captured["input"] = kw.get("input")  # None olmalı — passphrase yok
        Path(argv[argv.index("--output") + 1]).write_bytes(b"GPG-PUBKEY-ENC")
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(vb_mod.subprocess, "run", fake_run)
    result = encrypt_backup_recipient(
        plain, out, recipient="alice@example.com", gpg_bin="/fake/gpg",
    )
    assert result == out
    argv = captured["argv"]
    assert argv[0] == "/fake/gpg"
    assert "--encrypt" in argv
    idx_r = argv.index("--recipient")
    assert argv[idx_r + 1] == "alice@example.com"
    idx_t = argv.index("--trust-model")
    assert argv[idx_t + 1] == "always"
    # Passphrase argv'de veya stdin'de YOK (asimetrik)
    assert "--passphrase-fd" not in argv
    assert captured["input"] is None


def test_073_encrypt_recipient_exit_kod_hata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    plain = tmp_path / "p.tar.gz"
    plain.write_bytes(b"data")

    class _R:
        returncode = 2
        stdout = ""
        stderr = "gpg: unusable public key\n"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _R())
    with pytest.raises(VaultBackupError, match="gpg encrypt hatası"):
        encrypt_backup_recipient(plain, tmp_path / "out.gpg",
                                 recipient="unknown@x", gpg_bin="/fake/gpg")


# ═════════════════════════════════════════════════════════════════════
# CLI: vault backup --recipient
# ═════════════════════════════════════════════════════════════════════


def _fake_gpg_pubkey_run(argv, **kw):
    """Fake pubkey encrypt: --output dosyasını üret."""
    for i, a in enumerate(argv):
        if a == "--output":
            Path(argv[i + 1]).write_bytes(b"GPG-PUBKEY")
    class _R:
        returncode = 0
        stdout = ""
        stderr = ""
    return _R()


def test_073_cli_backup_recipient_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--recipient KEY_ID → .tar.gz.gpg üretilir, plain silinir."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    monkeypatch.setattr(vb_mod.subprocess, "run", _fake_gpg_pubkey_run)
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    out_plain = tmp_path / "y.tar.gz"
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(out_plain),
        "--recipient", "alice@example.com",
    ])
    assert rc == 0
    assert not out_plain.exists()
    enc = tmp_path / "y.tar.gz.gpg"
    assert enc.is_file()
    out = capsys.readouterr().out
    assert "asimetrik şifrelendi" in out
    assert "alice@example.com" in out
    # Audit
    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "encrypt-recipient" in audit_txt


def test_073_cli_backup_encrypt_recipient_mutex_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--encrypt + --recipient → exit 2 SPEC HATASI (mutex)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(tmp_path / "y.tar.gz"),
        "--encrypt", "s",
        "--recipient", "alice@x",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--encrypt ve --recipient" in err


def test_073_cli_backup_recipient_gpg_hata_exit_6(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})

    class _R:
        returncode = 2
        stdout = ""
        stderr = "gpg: no such public key"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _R())
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(tmp_path / "y.tar.gz"),
        "--recipient", "nobody@x",
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "SIFRELEME HATASI" in err


def test_073_cli_backup_recipient_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--recipient yoksa SPEC 041 default plain backup (bit-uyumlu)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    out = tmp_path / "y.tar.gz"
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()  # plain
    assert not (tmp_path / "y.tar.gz.gpg").exists()

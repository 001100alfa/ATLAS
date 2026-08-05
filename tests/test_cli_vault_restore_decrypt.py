"""SPEC 066 — atlas vault restore --decrypt (GPG symmetric)."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory import vault_backup as vb_mod
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    backup_vault,
    decrypt_backup,
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
# decrypt_backup (birim, subprocess mock)
# ═════════════════════════════════════════════════════════════════════


def test_066_decrypt_kaynak_yok_hata(tmp_path: Path) -> None:
    with pytest.raises(VaultBackupError, match="kaynak yok"):
        decrypt_backup(
            tmp_path / "yok.gpg",
            tmp_path / "out.tar.gz",
            passphrase="s",
            gpg_bin="/fake/gpg",
        )


def test_066_decrypt_bos_passphrase(tmp_path: Path) -> None:
    enc = tmp_path / "e.tar.gz.gpg"
    enc.write_bytes(b"ENC")
    with pytest.raises(VaultBackupError, match="passphrase bo"):
        decrypt_backup(enc, tmp_path / "out.tar.gz",
                       passphrase="", gpg_bin="/fake/gpg")


def test_066_decrypt_gpg_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    enc = tmp_path / "e.tar.gz.gpg"
    enc.write_bytes(b"ENC")
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: None)
    with pytest.raises(VaultBackupError, match="gpg bulunamadı"):
        decrypt_backup(enc, tmp_path / "out.tar.gz", passphrase="s")


def test_066_decrypt_argv_ve_stdin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """gpg --decrypt --passphrase-fd 0 --output <out> <enc>; stdin passphrase."""
    enc = tmp_path / "e.tar.gz.gpg"
    enc.write_bytes(b"ENC")
    out = tmp_path / "out.tar.gz"
    captured: dict = {}

    class _R:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(argv, **kw):
        captured["argv"] = list(argv)
        captured["input"] = kw.get("input")
        out.write_bytes(b"PLAIN-TAR")
        return _R()

    monkeypatch.setattr(vb_mod.subprocess, "run", fake_run)
    result = decrypt_backup(enc, out, passphrase="secret", gpg_bin="/fake/gpg")
    assert result == out
    assert captured["input"] == "secret"
    argv = captured["argv"]
    assert argv[0] == "/fake/gpg"
    assert "--decrypt" in argv
    idx_p = argv.index("--passphrase-fd")
    assert argv[idx_p + 1] == "0"
    idx_o = argv.index("--output")
    assert argv[idx_o + 1] == str(out)
    assert argv[-1] == str(enc)


def test_066_decrypt_gpg_exit_kod_hata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    enc = tmp_path / "e.tar.gz.gpg"
    enc.write_bytes(b"ENC")

    class _R:
        returncode = 2
        stdout = ""
        stderr = "gpg: bad passphrase\n"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _R())
    with pytest.raises(VaultBackupError, match="gpg decrypt hatası"):
        decrypt_backup(enc, tmp_path / "out.tar.gz",
                       passphrase="s", gpg_bin="/fake/gpg")


# ═════════════════════════════════════════════════════════════════════
# CLI: vault restore --decrypt
# ═════════════════════════════════════════════════════════════════════


def _make_real_backup_then_encrypt(tmp_path: Path) -> Path:
    """Gerçek plain backup üret; sonra fake gpg ile "encrypt" (kopyala)."""
    v = tmp_path / "src-vault"
    _make_vault(v, {"a.md": "orjinal-icerik", "daily/x.md": "gunluk"})
    plain = tmp_path / "b.tar.gz"
    backup_vault(v, plain)
    # Fake encrypt: sadece kopyala (test amaçlı; gerçek gpg olmadan)
    enc = tmp_path / "b.tar.gz.gpg"
    enc.write_bytes(plain.read_bytes())  # sözde encrypted
    plain.unlink()  # plain yok
    return enc


def _fake_gpg_decrypt(argv, **kw):
    """Fake decrypt: input dosyayı output'a kopyala (identity)."""
    inp = argv[-1]
    out = argv[argv.index("--output") + 1]
    Path(out).write_bytes(Path(inp).read_bytes())
    class _R:
        returncode = 0
        stdout = ""
        stderr = ""
    return _R()


def test_066_cli_restore_decrypt_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--decrypt PASSPHRASE + .tar.gz.gpg + --apply → restore başarılı."""
    _env(monkeypatch, tmp_path)
    enc = _make_real_backup_then_encrypt(tmp_path)
    monkeypatch.setattr(vb_mod.subprocess, "run", _fake_gpg_decrypt)
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    target = tmp_path / "restored-vault"
    rc = main([
        "vault", "restore", str(enc),
        "--apply",
        "--decrypt", "secret",
        "--vault-root", str(target),
    ])
    assert rc == 0
    # Restore doğrulama
    assert (target / "a.md").read_text(encoding="utf-8") == "orjinal-icerik"
    assert (target / "daily" / "x.md").read_text(encoding="utf-8") == "gunluk"
    # Audit: decrypt + restore
    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "decrypt" in audit_txt
    assert "restore" in audit_txt
    # Temp plain dosya silinmiş
    tmp_files = list(target.parent.glob(".vault-restore-decrypt-*.tar.gz"))
    assert tmp_files == []


def test_066_cli_restore_decrypt_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dry-run + --decrypt → 'GPG decrypt → restore (SPEC 066)' mesajı."""
    _env(monkeypatch, tmp_path)
    enc = _make_real_backup_then_encrypt(tmp_path)
    rc = main([
        "vault", "restore", str(enc),
        "--decrypt", "s",
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "GPG decrypt" in out


def test_066_cli_restore_decrypt_bos_passphrase_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    enc = _make_real_backup_then_encrypt(tmp_path)
    rc = main([
        "vault", "restore", str(enc),
        "--apply",
        "--decrypt", "",  # explicit boş
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "passphrase boş" in err


def test_066_cli_restore_decrypt_gpg_hata_exit_6(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    enc = _make_real_backup_then_encrypt(tmp_path)

    class _R:
        returncode = 2
        stdout = ""
        stderr = "gpg: passphrase yanlis"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _R())
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    rc = main([
        "vault", "restore", str(enc),
        "--apply",
        "--decrypt", "s",
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "DECRYPT HATASI" in err


def test_066_cli_restore_gpg_uzanti_uyari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """.gpg uzantısı + --decrypt YOK → UYARI (nazik auto-detect)."""
    _env(monkeypatch, tmp_path)
    enc = _make_real_backup_then_encrypt(tmp_path)
    rc = main([
        "vault", "restore", str(enc),
        "--vault-root", str(tmp_path / "yeni"),
    ])
    assert rc == 0  # dry-run, hata yok
    err = capsys.readouterr().err
    assert "UYARI" in err
    assert ".gpg uzantılı ama --decrypt verilmedi" in err


def test_066_cli_restore_bit_uyumlu_decrypt_yoksa(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--decrypt yoksa + plain .tar.gz → SPEC 041 default (bit-uyumlu)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "src-vault"
    _make_vault(v, {"a.md": "ok"})
    plain = tmp_path / "b.tar.gz"
    backup_vault(v, plain)
    target = tmp_path / "restored"
    rc = main([
        "vault", "restore", str(plain), "--apply",
        "--vault-root", str(target),
    ])
    assert rc == 0
    assert (target / "a.md").read_text(encoding="utf-8") == "ok"

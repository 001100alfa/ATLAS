"""SPEC 063 — vault backup --encrypt GPG symmetric (subprocess mock)."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory import vault_backup as vb_mod
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    _find_gpg_bin,
    encrypt_backup,
)


def _make_vault(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.delenv("ATLAS_BACKUP_PASSPHRASE", raising=False)
    monkeypatch.delenv("ATLAS_GPG_BIN", raising=False)


# ═════════════════════════════════════════════════════════════════════
# _find_gpg_bin
# ═════════════════════════════════════════════════════════════════════


def test_063_find_gpg_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """ATLAS_GPG_BIN env override öncelikli."""
    override = tmp_path / "custom-gpg"
    override.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_GPG_BIN", str(override))
    result = _find_gpg_bin()
    assert result == str(override)


def test_063_find_gpg_env_yok_ise_none_veya_which(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env yok + portable yok → shutil.which sonucu (kurulu ise str)."""
    monkeypatch.delenv("ATLAS_GPG_BIN", raising=False)
    # tools/gpg/ yok kabulü (test cwd tmp_path olabilir; portable görmez)
    result = _find_gpg_bin()
    # Ya sistemde gpg vardır ya yoktur — tip kontrolü yeterli
    assert result is None or isinstance(result, str)


# ═════════════════════════════════════════════════════════════════════
# encrypt_backup — subprocess mock
# ═════════════════════════════════════════════════════════════════════


def test_063_encrypt_kaynak_yok_hata(tmp_path: Path) -> None:
    with pytest.raises(VaultBackupError, match="kaynak yok"):
        encrypt_backup(
            tmp_path / "yok.tar.gz",
            tmp_path / "out.gpg",
            passphrase="secret",
            gpg_bin="/fake/gpg",
        )


def test_063_encrypt_bos_passphrase_hata(tmp_path: Path) -> None:
    plain = tmp_path / "x.tar.gz"
    plain.write_bytes(b"data")
    with pytest.raises(VaultBackupError, match="passphrase bo"):
        encrypt_backup(plain, tmp_path / "out.gpg", passphrase="",
                       gpg_bin="/fake/gpg")


def test_063_encrypt_gpg_yok_hata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    plain = tmp_path / "x.tar.gz"
    plain.write_bytes(b"data")
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: None)
    with pytest.raises(VaultBackupError, match="gpg bulunamadı"):
        encrypt_backup(plain, tmp_path / "out.gpg", passphrase="s")


def test_063_encrypt_argv_ve_stdin_dogru(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """gpg argv: --batch --yes --symmetric --cipher-algo AES256
    --passphrase-fd 0 --output <out> <plain>. Passphrase input."""
    plain = tmp_path / "x.tar.gz"
    plain.write_bytes(b"data")
    out = tmp_path / "x.tar.gz.gpg"
    captured: dict = {}

    class _Fake:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(argv, **kw):  # type: ignore[no-untyped-def]
        captured["argv"] = list(argv)
        captured["input"] = kw.get("input")
        # Simüle çıktı dosyası
        out.write_bytes(b"ENCRYPTED")
        return _Fake()

    monkeypatch.setattr(vb_mod.subprocess, "run", fake_run)
    result = encrypt_backup(plain, out, passphrase="secret", gpg_bin="/fake/gpg")
    assert result == out
    assert captured["input"] == "secret"
    argv = captured["argv"]
    assert argv[0] == "/fake/gpg"
    assert "--batch" in argv
    assert "--yes" in argv
    assert "--symmetric" in argv
    idx_c = argv.index("--cipher-algo")
    assert argv[idx_c + 1] == "AES256"
    idx_p = argv.index("--passphrase-fd")
    assert argv[idx_p + 1] == "0"
    idx_o = argv.index("--output")
    assert argv[idx_o + 1] == str(out)


def test_063_encrypt_gpg_exit_kod_hata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """gpg exit ≠0 → VaultBackupError + stderr metnini içerir."""
    plain = tmp_path / "x.tar.gz"
    plain.write_bytes(b"data")

    class _Fake:
        returncode = 2
        stdout = ""
        stderr = "gpg: hata: yanlış passphrase\n"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _Fake())
    with pytest.raises(VaultBackupError, match="gpg hatası"):
        encrypt_backup(plain, tmp_path / "out.gpg", passphrase="s",
                       gpg_bin="/fake/gpg")


def test_063_encrypt_subprocess_oserror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    plain = tmp_path / "x.tar.gz"
    plain.write_bytes(b"data")

    def bad_run(*a, **kw):
        raise OSError("[Errno 2] gpg not found")

    monkeypatch.setattr(vb_mod.subprocess, "run", bad_run)
    with pytest.raises(VaultBackupError, match="gpg çalıştırılamadı"):
        encrypt_backup(plain, tmp_path / "out.gpg", passphrase="s",
                       gpg_bin="/fake/gpg")


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas vault backup --encrypt
# ═════════════════════════════════════════════════════════════════════


def test_063_cli_backup_encrypt_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--encrypt PASSPHRASE → .tar.gz.gpg üretilir, plain silinir."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})

    def fake_run(argv, **kw):
        # gpg output dosyasını üret
        for i, a in enumerate(argv):
            if a == "--output":
                Path(argv[i + 1]).write_bytes(b"GPG-ENC")
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(vb_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    out_plain = tmp_path / "yedek.tar.gz"
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(out_plain),
        "--encrypt", "mysecret",
    ])
    assert rc == 0
    # Plain silinmiş, .gpg mevcut
    assert not out_plain.exists()
    enc = tmp_path / "yedek.tar.gz.gpg"
    assert enc.is_file()
    out = capsys.readouterr().out
    assert "vault yedeği yazıldı" in out
    assert "vault yedeği şifrelendi" in out


def test_063_cli_backup_encrypt_bos_passphrase_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--encrypt boş string + env yok → exit 2."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})

    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(tmp_path / "y.tar.gz"),
        "--encrypt", "",  # explicit boş
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "passphrase boş" in err


def test_063_cli_backup_encrypt_env_passphrase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--encrypt bayraksız + ATLAS_BACKUP_PASSPHRASE env → env değerini alır."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_BACKUP_PASSPHRASE", "env-secret")
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})

    captured: dict = {}

    def fake_run(argv, **kw):
        captured["input"] = kw.get("input")
        for i, a in enumerate(argv):
            if a == "--output":
                Path(argv[i + 1]).write_bytes(b"GPG-ENC")
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(vb_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(tmp_path / "y.tar.gz"),
        "--encrypt",  # bayraksız → const=env değeri
    ])
    assert rc == 0
    assert captured["input"] == "env-secret"


def test_063_cli_backup_encrypt_gpg_hata_exit_6(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """gpg exit ≠0 → CLI exit 6 (mevcut backup hata sınıfı)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})

    class _R:
        returncode = 2
        stdout = ""
        stderr = "gpg: passphrase yanlis"

    monkeypatch.setattr(vb_mod.subprocess, "run", lambda *a, **kw: _R())
    monkeypatch.setattr(vb_mod, "_find_gpg_bin", lambda: "/fake/gpg")

    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(tmp_path / "y.tar.gz"),
        "--encrypt", "s",
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "SIFRELEME HATASI" in err


def test_063_cli_backup_encrypt_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--encrypt yoksa SPEC 041 default davranış (bit-uyumlu)."""
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
    assert out.is_file()
    assert not (tmp_path / "y.tar.gz.gpg").exists()

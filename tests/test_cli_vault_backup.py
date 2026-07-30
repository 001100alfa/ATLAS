"""SPEC 041 — atlas vault backup + restore testleri."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    backup_vault,
    restore_vault,
)


def _make_vault(root: Path, files: dict[str, str]) -> None:
    """Sahte vault: her `<folder>/<name>.md` → içerik."""
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


# ═════════════════════════════════════════════════════════════════════
# backup_vault + restore_vault (birim)
# ═════════════════════════════════════════════════════════════════════


def test_041_backup_vault_yok_hata(tmp_path: Path) -> None:
    with pytest.raises(VaultBackupError, match="vault yok"):
        backup_vault(tmp_path / "yok", tmp_path / "backup.tar.gz")


def test_041_backup_vault_tar_yazilir(tmp_path: Path) -> None:
    """`vault/` → `.tar.gz` içinde 'vault/notes/a.md' bulunur."""
    v = tmp_path / "vault"
    _make_vault(v, {"notes/a.md": "A içerik", "daily/2026-07-30.md": "günlük"})
    out = tmp_path / "backup.tar.gz"
    result = backup_vault(v, out)
    assert result == out
    assert out.is_file()
    with tarfile.open(out, "r:gz") as tar:
        names = tar.getnames()
    assert "vault/notes/a.md" in names
    assert "vault/daily/2026-07-30.md" in names


def test_041_restore_vault_basari(tmp_path: Path) -> None:
    """Backup → restore → dosyalar geri geliyor."""
    v = tmp_path / "vault"
    _make_vault(v, {"notes/a.md": "orjinal", "daily/x.md": "y"})
    tar = tmp_path / "backup.tar.gz"
    backup_vault(v, tar)

    target = tmp_path / "restored-vault"
    result = restore_vault(tar, target)
    assert result == target
    assert (target / "notes" / "a.md").read_text(encoding="utf-8") == "orjinal"
    assert (target / "daily" / "x.md").read_text(encoding="utf-8") == "y"


def test_041_restore_hedef_bos_degil_hata(tmp_path: Path) -> None:
    """Hedef mevcut ve boş değil → VaultBackupError."""
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "x"})
    tar = tmp_path / "b.tar.gz"
    backup_vault(v, tar)

    target = tmp_path / "vault2"
    target.mkdir()
    (target / "eski.md").write_text("dolu", encoding="utf-8")

    with pytest.raises(VaultBackupError, match="zaten var"):
        restore_vault(tar, target)


def test_041_restore_path_traversal_reddedilir(tmp_path: Path) -> None:
    """Kötücül tar (`../evil`) → VaultBackupError."""
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        info = tarfile.TarInfo(name="../evil.txt")
        info.size = 0
        tar.addfile(info)
    with pytest.raises(VaultBackupError, match="güvensiz"):
        restore_vault(bad, tmp_path / "vault-restored")


def test_041_restore_beklenmeyen_kok_reddedilir(tmp_path: Path) -> None:
    """Tar kökü 'vault' değilse hata."""
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        info = tarfile.TarInfo(name="baska/x.md")
        info.size = 0
        tar.addfile(info)
    with pytest.raises(VaultBackupError, match="beklenmeyen kök"):
        restore_vault(bad, tmp_path / "vault-restored")


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas vault backup / restore
# ═════════════════════════════════════════════════════════════════════


def test_041_cli_backup_out_yolu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas vault backup --out X` → X'e yazar."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    out = tmp_path / "yedek.tar.gz"
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    out_str = capsys.readouterr().out
    assert "vault yedeği yazıldı" in out_str


def test_041_cli_backup_varsayilan_yol(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--out` yok → `<archive>/vault-...tar.gz` yazılır."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    arc = tmp_path / "arc"
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    tars = list(arc.glob("vault-*.tar.gz"))
    assert len(tars) == 1


def test_041_cli_backup_vault_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "backup",
        "--vault-root", str(tmp_path / "yok"),
        "--out", str(tmp_path / "b.tar.gz"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_041_cli_restore_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dry-run: plan basar, yazmaz."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    tar = tmp_path / "b.tar.gz"
    backup_vault(v, tar)

    target = tmp_path / "restored"
    rc = main([
        "vault", "restore", str(tar),
        "--vault-root", str(target),
    ])
    assert rc == 0
    assert not target.exists()
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "Uygulamak için: atlas vault restore" in out


def test_041_cli_restore_apply_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--apply → gerçek extract."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "orjinal", "daily/d.md": "gunluk"})
    tar = tmp_path / "b.tar.gz"
    backup_vault(v, tar)

    target = tmp_path / "restored"
    rc = main([
        "vault", "restore", str(tar), "--apply",
        "--vault-root", str(target),
    ])
    assert rc == 0
    assert (target / "a.md").read_text(encoding="utf-8") == "orjinal"
    assert (target / "daily" / "d.md").read_text(encoding="utf-8") == "gunluk"


def test_041_cli_restore_tar_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "restore", str(tmp_path / "yok.tar.gz"),
        "--vault-root", str(tmp_path / "v"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_041_cli_restore_cakisma_exit_3(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Hedef mevcut + boş değil + --apply → exit 3."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    tar = tmp_path / "b.tar.gz"
    backup_vault(v, tar)

    target = tmp_path / "dolu"
    target.mkdir()
    (target / "eski.md").write_text("var", encoding="utf-8")

    rc = main([
        "vault", "restore", str(tar), "--apply",
        "--vault-root", str(target),
    ])
    assert rc == 3
    err = capsys.readouterr().err
    assert "zaten var" in err


def test_041_cli_backup_audit_kaydi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Backup → audit satırı (`atlas-vault`, `backup`)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(tmp_path / "b.tar.gz"),
    ])
    assert rc == 0
    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "atlas-vault" in audit_txt
    assert "backup" in audit_txt

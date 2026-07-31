"""SPEC 041 — atlas vault backup + restore testleri."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault_backup import (
    VaultBackupError,
    backup_vault,
    prune_backups,
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


# ═════════════════════════════════════════════════════════════════════
# SPEC 041.1 — prune_backups (birim) + CLI --auto / --keep
# ═════════════════════════════════════════════════════════════════════


def _touch_backup(archive_root: Path, name: str, mtime: float) -> Path:
    """Yardımcı: boş `.tar.gz` yaratıp mtime'ı zorlar."""
    import os as _os
    archive_root.mkdir(parents=True, exist_ok=True)
    p = archive_root / name
    p.write_bytes(b"\x1f\x8b\x08\x00")  # boş gzip header — içerik denetlenmiyor
    _os.utime(p, (mtime, mtime))
    return p


def test_041_1_prune_backups_keep_1_siler(tmp_path: Path) -> None:
    """3 yedek + keep=1 → 1 en yeni kalır, 2 eski silinir."""
    arc = tmp_path / "archive"
    old = _touch_backup(arc, "vault-2026-01-01-0000.tar.gz", 1_000.0)
    mid = _touch_backup(arc, "vault-2026-02-01-0000.tar.gz", 2_000.0)
    new = _touch_backup(arc, "vault-2026-03-01-0000.tar.gz", 3_000.0)

    deleted = prune_backups(arc, keep=1)

    assert set(deleted) == {old, mid}
    assert not old.exists()
    assert not mid.exists()
    assert new.exists()


def test_041_1_prune_backups_keep_gte_toplam_hicbir_sey_silmez(
    tmp_path: Path,
) -> None:
    """keep >= dosya sayısı → silme yok, boş liste."""
    arc = tmp_path / "archive"
    a = _touch_backup(arc, "vault-a.tar.gz", 1_000.0)
    b = _touch_backup(arc, "vault-b.tar.gz", 2_000.0)

    deleted = prune_backups(arc, keep=5)

    assert deleted == []
    assert a.exists() and b.exists()


def test_041_1_prune_backups_dogru_desene_dokunmaz(tmp_path: Path) -> None:
    """`vault-*.tar.gz` DIŞI dosyalar korunur; keep=1 sadece backup'ları etkiler."""
    arc = tmp_path / "archive"
    _touch_backup(arc, "vault-eski.tar.gz", 1_000.0)
    _touch_backup(arc, "vault-yeni.tar.gz", 2_000.0)
    baska = arc / "task-007-2026-01-01.tar.gz"  # SPEC 007 arşivi — dokunma
    baska.write_bytes(b"x")
    okuma = arc / "README.txt"
    okuma.write_text("koru", encoding="utf-8")

    prune_backups(arc, keep=1)

    assert baska.exists()
    assert okuma.exists()


def test_041_1_prune_backups_keep_sifir_hata(tmp_path: Path) -> None:
    with pytest.raises(VaultBackupError, match=">= 1"):
        prune_backups(tmp_path, keep=0)


def test_041_1_prune_backups_archive_yok_bos_liste(tmp_path: Path) -> None:
    """Cron nazikliği: `archive_root` yoksa hata değil, boş liste."""
    assert prune_backups(tmp_path / "yok", keep=3) == []


def test_041_1_cli_backup_auto_default_yol(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--auto` → archive_root'a vault-*.tar.gz yazılır, audit=backup-auto."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    arc = tmp_path / "arc"
    rc = main([
        "vault", "backup", "--auto",
        "--vault-root", str(v),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    tars = list(arc.glob("vault-*.tar.gz"))
    assert len(tars) == 1
    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "backup-auto" in audit_txt


def test_041_1_cli_backup_auto_out_cakisma_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    rc = main([
        "vault", "backup", "--auto",
        "--vault-root", str(v),
        "--out", str(tmp_path / "b.tar.gz"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--auto ve --out" in err


def test_041_1_cli_backup_keep_retention(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Var olan 3 yedek + backup + --keep 2 → 2 kalır (yeni + en yeni eski)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    arc = tmp_path / "arc"
    en_eski = _touch_backup(arc, "vault-2020-01-01-0000.tar.gz", 1_000.0)
    orta = _touch_backup(arc, "vault-2021-01-01-0000.tar.gz", 2_000.0)
    en_yeni_eski = _touch_backup(arc, "vault-2022-01-01-0000.tar.gz", 3_000.0)

    rc = main([
        "vault", "backup", "--auto",
        "--vault-root", str(v),
        "--archive-root", str(arc),
        "--keep", "2",
    ])
    assert rc == 0
    kalan = sorted(arc.glob("vault-*.tar.gz"))
    # Yeni yazılan (bugün) + en yeni eski (3000.0 mtime) kalır;
    # ortada (2000.0) ve en eski (1000.0) silinir.
    assert en_yeni_eski in kalan
    assert orta not in kalan
    assert en_eski not in kalan
    assert len(kalan) == 2

    out = capsys.readouterr().out
    assert "prune:" in out
    audit_txt = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert audit_txt.count('"prune"') == 2


def test_041_1_cli_backup_out_ile_keep_uyarisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--out` + `--keep` → uyarı, retention YOK, backup başarılı."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "vault"
    _make_vault(v, {"a.md": "ok"})
    out = tmp_path / "yedek.tar.gz"
    # archive-root'da eski dosya olsun; keep uygulansaydı silinirdi
    arc = tmp_path / "arc"
    eski = _touch_backup(arc, "vault-2020-01-01.tar.gz", 500.0)
    rc = main([
        "vault", "backup",
        "--vault-root", str(v),
        "--out", str(out),
        "--archive-root", str(arc),
        "--keep", "1",
    ])
    assert rc == 0
    assert out.is_file()
    assert eski.exists()  # retention atlandı → silinmedi
    err = capsys.readouterr().err
    assert "UYARI" in err
    assert "--keep YOK sayıldı" in err


def test_041_1_cli_backup_keep_sifir_exit_2(
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
        "--keep", "0",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--keep" in err

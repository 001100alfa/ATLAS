"""SPEC 041: Vault yedekleme + geri yükleme.

`vault/` dizinini `.tar.gz` sarmalar ve geri açar. SPEC 033 archive
kalıbının kardeşi — aynı path traversal koruması + `filter="data"`
güvenli extract + Windows kolon reddi.

Backup üretilen `.tar.gz` içinde vault kökü `vault/` altındadır
(arcname sabit). Restore çakışma → RestoreError; path traversal veya
kolon → RestoreError.
"""

from __future__ import annotations

import shutil
import tarfile
from datetime import datetime
from pathlib import Path


class VaultBackupError(RuntimeError):
    """SPEC 041: Vault yedekleme/geri yükleme hatası."""


_ARCNAME = "vault"  # tar içindeki kök klasör adı


def backup_vault(vault_root: Path, out_path: Path) -> Path:
    """SPEC 041: `vault_root` dizinini `.tar.gz` olarak `out_path`'a yaz.

    - `out_path` dosya yolu (klasör değil); üst klasörü yoksa oluşturulur.
    - Tar içindeki kök `_ARCNAME` = "vault" — restore tarafında kanonik.
    - Vault yoksa `VaultBackupError`.

    Döner: yazılan `.tar.gz` yolu.
    """
    if not vault_root.is_dir():
        raise VaultBackupError(f"vault yok: {vault_root}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(out_path, "w:gz") as tar:
            tar.add(vault_root, arcname=_ARCNAME)
    except (OSError, tarfile.TarError) as exc:
        raise VaultBackupError(f"yedek yazılamadı: {exc}") from exc
    return out_path


def default_backup_path(archive_root: Path) -> Path:
    """SPEC 041: `<archive_root>/vault-YYYY-MM-DD-HHMM.tar.gz`."""
    ts = datetime.now().strftime("%Y-%m-%d-%H%M")
    return archive_root / f"vault-{ts}.tar.gz"


def prune_backups(archive_root: Path, keep: int) -> list[Path]:
    """SPEC 041.1: `<archive_root>/vault-*.tar.gz` yedeklerinden retention.

    Dosyaları mtime desc sıraya koyar (en yeni önce); ilk `keep` tanesini
    tutar, geri kalanları siler. Sadece `vault-*.tar.gz` desenine uyan
    dosyalara dokunur — diğer dosya/klasörler korunur.

    - `keep < 1` → `VaultBackupError` (SPEC HATASI eşleniği).
    - `archive_root` yok → boş liste (hata değil, cron için nazik).
    - Silme hatası (`OSError`) → `VaultBackupError`.

    Döner: silinen dosya yollarının listesi (kararlı sıralı).
    """
    if keep < 1:
        raise VaultBackupError(f"keep >= 1 olmalı: {keep}")
    if not archive_root.is_dir():
        return []
    candidates = sorted(
        archive_root.glob("vault-*.tar.gz"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    to_delete = candidates[keep:]
    deleted: list[Path] = []
    for p in to_delete:
        try:
            p.unlink()
        except OSError as exc:
            raise VaultBackupError(f"prune başarısız: {p}: {exc}") from exc
        deleted.append(p)
    return deleted


def restore_vault(tar_path: Path, target_root: Path) -> Path:
    """SPEC 041: `.tar.gz`'i `target_root`'a aç.

    - Tar kökü `_ARCNAME` sabit; başka kök → hata.
    - `target_root` zaten var + boş değil → çakışma (`VaultBackupError`).
    - `target_root` yoksa oluşturulur.
    - Her üye elle kontrol: path traversal (`..`), mutlak yol, kolon
      (Windows NTFS ADS), beklenmeyen kök reddedilir.
    - `filter="data"` ile ekstra güvenlik.

    Döner: geri yüklenen `target_root` yolu.
    """
    if not tar_path.is_file():
        raise VaultBackupError(f"yedek dosyası yok: {tar_path}")
    if target_root.exists() and any(target_root.iterdir()):
        raise VaultBackupError(
            f"hedef zaten var ve boş değil: {target_root} "
            "(önce silin veya taşıyın)"
        )
    parent = target_root.parent
    parent.mkdir(parents=True, exist_ok=True)
    # Temporary extract dir — sonra rename ederiz
    tmp_extract = parent / f".vault-restore-{datetime.now().strftime('%H%M%S')}"
    tmp_extract.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            members = tar.getmembers()
            for m in members:
                name = m.name.replace("\\", "/")
                if name.startswith("/") or ".." in name.split("/"):
                    raise VaultBackupError(
                        f"güvensiz üye adı (path traversal?): {m.name}"
                    )
                if ":" in name:
                    raise VaultBackupError(
                        f"güvensiz üye adı (kolon): {m.name}"
                    )
                first = name.split("/", 1)[0]
                if first != _ARCNAME:
                    raise VaultBackupError(
                        f"beklenmeyen kök: '{first}' (bekleniyor: '{_ARCNAME}')"
                    )
            tar.extractall(tmp_extract, filter="data")  # noqa: S202
        extracted = tmp_extract / _ARCNAME
        if not extracted.is_dir():
            raise VaultBackupError(f"yedek boş: {tar_path}")
        # Şimdi rename → hedef
        if target_root.exists():
            # Boş dizin ise sil ve rename yap
            target_root.rmdir()
        extracted.rename(target_root)
    except (OSError, tarfile.TarError) as exc:
        # Kısmi extract varsa temizle
        raise VaultBackupError(f"extract başarısız: {exc}") from exc
    finally:
        if tmp_extract.exists():
            shutil.rmtree(tmp_extract, ignore_errors=True)
    return target_root

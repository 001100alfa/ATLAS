"""SPEC 041 + 063: Vault yedekleme + geri yükleme + GPG şifreleme.

`vault/` dizinini `.tar.gz` sarmalar ve geri açar. SPEC 033 archive
kalıbının kardeşi — aynı path traversal koruması + `filter="data"`
güvenli extract + Windows kolon reddi.

Backup üretilen `.tar.gz` içinde vault kökü `vault/` altındadır
(arcname sabit). Restore çakışma → RestoreError; path traversal veya
kolon → RestoreError.

SPEC 063: `encrypt_backup` yardımcı — GPG symmetric (AES256) ile
`.tar.gz.gpg` üretir. Passphrase stdin ile (`--passphrase-fd 0`)
geçilir; komut satırı history'sinde görünmez.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

from atlas_core.utils.safe_tar import UnsafeTarMemberError, verify_tar_members


class VaultBackupError(RuntimeError):
    """SPEC 041: Vault yedekleme/geri yükleme hatası."""


_ARCNAME = "vault"  # tar içindeki kök klasör adı


# ═════════════════════════════════════════════════════════════════════
# SPEC 063: GPG symmetric encryption yardımcıları
# ═════════════════════════════════════════════════════════════════════


def _find_gpg_bin() -> str | None:
    """SPEC 063: gpg binary yolunu bul.

    Öncelik: `ATLAS_GPG_BIN` env override → depo-yerel `tools/gpg/gpg[.exe]`
    → sistem PATH (`shutil.which("gpg")`).
    """
    override = os.environ.get("ATLAS_GPG_BIN", "").strip()
    if override and Path(override).is_file():
        return override
    # Portable depo-yerel
    portable_name = "gpg.exe" if sys.platform == "win32" else "gpg"
    portable = Path("tools/gpg") / portable_name
    if portable.is_file():
        return str(portable.resolve())
    return shutil.which("gpg")


def encrypt_backup(
    plain_path: Path,
    out_path: Path,
    passphrase: str,
    *,
    gpg_bin: str | None = None,
    cipher: str = "AES256",
) -> Path:
    """SPEC 063: `plain_path` dosyasını GPG symmetric ile şifrele.

    - `gpg --batch --yes --symmetric --cipher-algo <cipher> --passphrase-fd 0
      --output <out_path> <plain_path>`
    - Passphrase stdin ile geçirilir (komut satırı history'sinde görünmez).
    - `out_path.parent` yoksa oluşturulur.
    - Başarı → `out_path` döner; hata → `VaultBackupError`.

    `gpg_bin=None` → `_find_gpg_bin()` otomatik bulur.
    """
    if not plain_path.is_file():
        raise VaultBackupError(f"kaynak yok: {plain_path}")
    if not passphrase:
        raise VaultBackupError("passphrase boş olamaz")
    gpg = gpg_bin or _find_gpg_bin()
    if gpg is None:
        raise VaultBackupError(
            "gpg bulunamadı — ATLAS_GPG_BIN ver veya sisteme kur"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # `--yes` mevcut çıktıyı üzerine yazar (idempotent).
    args = [
        gpg, "--batch", "--yes",
        "--symmetric", "--cipher-algo", cipher,
        "--passphrase-fd", "0",
        "--output", str(out_path),
        str(plain_path),
    ]
    try:
        proc = subprocess.run(  # noqa: S603 - argv sabit + gpg yolu filtrelendi
            args,
            input=passphrase,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VaultBackupError(f"gpg çalıştırılamadı: {exc}") from exc
    if proc.returncode != 0:
        raise VaultBackupError(
            f"gpg hatası (exit {proc.returncode}): "
            f"{(proc.stderr or '').strip()[:200]}"
        )
    if not out_path.is_file():
        raise VaultBackupError(
            f"gpg başarılı ama çıktı yok: {out_path}"
        )
    return out_path


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


def combine_split_parts(first_part: Path) -> Path:
    """SPEC 102: `.001` başlayan parçaları birleştirip tek dosyaya yaz.

    - `first_part` `.001` uzantılı olmalı (aksi hâlde `VaultBackupError`).
    - Aynı base + `.NNN` (3 haneli) sıralı parçaları okur; eksik/boş
      → `VaultBackupError`.
    - Sonuç: birleştirilmiş geçici dosya `<base>.combined-<pid>` — çağıran
      restore + temp silme yapmalı (SPEC 066 kalıbı).
    - Parçaların orijinali korunur (silinmez).

    Döner: birleştirilmiş geçici dosya yolu.
    """
    if first_part.suffix != ".001":
        raise VaultBackupError(
            f"split first_part '.001' olmalı: {first_part.name}",
        )
    base = first_part.with_suffix("")  # `.001` sıyır → `<x>.tar.gz`
    if not first_part.is_file():
        raise VaultBackupError(f"split ilk parça yok: {first_part}")
    # Aynı base + .NNN deseni
    parts: list[Path] = []
    idx = 1
    while True:
        p = base.with_suffix(base.suffix + f".{idx:03d}")
        if not p.is_file():
            break
        parts.append(p)
        idx += 1
    if not parts:
        raise VaultBackupError(f"split hiç parça bulunamadı: {base.name}")
    tmp_out = base.parent / f".{base.name}.combined-{os.getpid()}"
    try:
        with tmp_out.open("wb") as fout:
            for p in parts:
                with p.open("rb") as fin:
                    shutil.copyfileobj(fin, fout)
    except OSError as exc:
        # Cleanup
        try:
            tmp_out.unlink()
        except OSError:
            pass
        raise VaultBackupError(f"split birleştirme IO hatası: {exc}") from exc
    return tmp_out


def split_backup(src: Path, size_mb: int) -> list[Path]:
    """SPEC 101: `src` dosyasını `size_mb * 1024 * 1024` byte parçalara böl.

    Çıktı: `<src>.001`, `<src>.002`, ... (3 haneli 1-based). Orijinal
    `src` silinir (space tasarrufu). Birleştirme:
    `cat <src>.* > <src>` (POSIX) veya `copy /b <src>.001+<src>.002 <src>`
    (Windows).

    - `size_mb < 1` → `VaultBackupError`.
    - Src yok → `VaultBackupError`.
    - IO hatası → `VaultBackupError`.

    Döner: yazılan parça dosya yolları listesi (sıralı).
    """
    if size_mb < 1:
        raise VaultBackupError(f"split size_mb >= 1 olmalı: {size_mb}")
    if not src.is_file():
        raise VaultBackupError(f"split kaynak yok: {src}")
    chunk_bytes = size_mb * 1024 * 1024
    parts: list[Path] = []
    try:
        with src.open("rb") as fin:
            idx = 1
            while True:
                buf = fin.read(chunk_bytes)
                if not buf:
                    break
                part_path = src.with_suffix(src.suffix + f".{idx:03d}")
                with part_path.open("wb") as fout:
                    fout.write(buf)
                parts.append(part_path)
                idx += 1
    except OSError as exc:
        raise VaultBackupError(f"split IO hatası: {exc}") from exc
    if not parts:
        # Boş src (0 byte) — tek boş parça oluştur (birleştirme sözleşmesi)
        part_path = src.with_suffix(src.suffix + ".001")
        part_path.write_bytes(b"")
        parts.append(part_path)
    try:
        src.unlink()
    except OSError as exc:
        raise VaultBackupError(f"split sonrası src silinemedi: {exc}") from exc
    return parts


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


def encrypt_backup_recipient(
    plain_path: Path,
    out_path: Path,
    recipient: str,
    *,
    gpg_bin: str | None = None,
) -> Path:
    """SPEC 073: `plain_path`'i GPG public-key ile şifrele.

    - `gpg --batch --yes --encrypt --recipient <KEY_ID> --trust-model
      always --output <out_path> <plain_path>`
    - Passphrase YOK (asimetrik — recipient keyring'te olmalı).
    - `--trust-model always`: kullanıcı KEY_ID trust'i doğrulanmadıysa
      da devam et (CI/automation dostluğu; kullanıcı sözleşme kabulü).
    - `out_path.parent` yoksa oluşturulur.
    - Başarı → `out_path` döner; hata → `VaultBackupError`.

    `gpg_bin=None` → `_find_gpg_bin()` otomatik bulur.
    """
    if not plain_path.is_file():
        raise VaultBackupError(f"kaynak yok: {plain_path}")
    if not recipient:
        raise VaultBackupError("recipient (KEY_ID) boş olamaz")
    gpg = gpg_bin or _find_gpg_bin()
    if gpg is None:
        raise VaultBackupError(
            "gpg bulunamadı — ATLAS_GPG_BIN ver veya sisteme kur"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        gpg, "--batch", "--yes",
        "--encrypt",
        "--recipient", recipient,
        "--trust-model", "always",
        "--output", str(out_path),
        str(plain_path),
    ]
    try:
        proc = subprocess.run(  # noqa: S603 - argv sabit + gpg yolu filtrelendi
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VaultBackupError(f"gpg çalıştırılamadı: {exc}") from exc
    if proc.returncode != 0:
        raise VaultBackupError(
            f"gpg encrypt hatası (exit {proc.returncode}): "
            f"{(proc.stderr or '').strip()[:200]}"
        )
    if not out_path.is_file():
        raise VaultBackupError(
            f"gpg başarılı ama çıktı yok: {out_path}"
        )
    return out_path


def decrypt_backup_recipient(
    encrypted_path: Path,
    out_path: Path,
    *,
    gpg_bin: str | None = None,
) -> Path:
    """SPEC 078: `.tar.gz.gpg` asimetrik (public-key) decrypt.

    - `gpg --batch --yes --decrypt --output <out> <encrypted>`
    - Passphrase YOK — private key gpg-agent üzerinden çözülür.
      Terminal etkileşimi olamayacağı için `--batch --yes` +
      gpg-agent'in kilit açması gerekir (kullanıcı önceden `gpg-agent
      --daemon` veya keyring unlock yapmış olmalı).
    - `out_path.parent` yoksa oluşturulur.
    - Başarı → `out_path`; hata → `VaultBackupError`.

    Not: symmetric decrypt için SPEC 066 `decrypt_backup` — o
    `--passphrase-fd 0` kullanır. Asimetrik için passphrase YOK.
    """
    if not encrypted_path.is_file():
        raise VaultBackupError(f"kaynak yok: {encrypted_path}")
    gpg = gpg_bin or _find_gpg_bin()
    if gpg is None:
        raise VaultBackupError(
            "gpg bulunamadı — ATLAS_GPG_BIN ver veya sisteme kur"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        gpg, "--batch", "--yes",
        "--decrypt",
        "--output", str(out_path),
        str(encrypted_path),
    ]
    try:
        proc = subprocess.run(  # noqa: S603 - argv sabit + gpg yolu filtrelendi
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VaultBackupError(f"gpg çalıştırılamadı: {exc}") from exc
    if proc.returncode != 0:
        raise VaultBackupError(
            f"gpg decrypt hatası (exit {proc.returncode}): "
            f"{(proc.stderr or '').strip()[:200]}"
        )
    if not out_path.is_file():
        raise VaultBackupError(
            f"gpg başarılı ama çıktı yok: {out_path}"
        )
    return out_path


def decrypt_backup(
    encrypted_path: Path,
    out_path: Path,
    passphrase: str,
    *,
    gpg_bin: str | None = None,
) -> Path:
    """SPEC 066: `.tar.gz.gpg` dosyasını GPG symmetric ile decrypt et.

    - `gpg --batch --yes --decrypt --passphrase-fd 0 --output <out>
      <encrypted>`
    - Passphrase stdin ile geçirilir.
    - `out_path.parent` yoksa oluşturulur.
    - Başarı → `out_path` döner; hata → `VaultBackupError`.

    `gpg_bin=None` → `_find_gpg_bin()` otomatik bulur.
    """
    if not encrypted_path.is_file():
        raise VaultBackupError(f"kaynak yok: {encrypted_path}")
    if not passphrase:
        raise VaultBackupError("passphrase boş olamaz")
    gpg = gpg_bin or _find_gpg_bin()
    if gpg is None:
        raise VaultBackupError(
            "gpg bulunamadı — ATLAS_GPG_BIN ver veya sisteme kur"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        gpg, "--batch", "--yes",
        "--decrypt",
        "--passphrase-fd", "0",
        "--output", str(out_path),
        str(encrypted_path),
    ]
    try:
        proc = subprocess.run(  # noqa: S603 - argv sabit + gpg yolu filtrelendi
            args,
            input=passphrase,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VaultBackupError(f"gpg çalıştırılamadı: {exc}") from exc
    if proc.returncode != 0:
        raise VaultBackupError(
            f"gpg decrypt hatası (exit {proc.returncode}): "
            f"{(proc.stderr or '').strip()[:200]}"
        )
    if not out_path.is_file():
        raise VaultBackupError(
            f"gpg başarılı ama çıktı yok: {out_path}"
        )
    return out_path


def prune_encrypted_backups(
    archive_root: Path, keep: int,
) -> list[Path]:
    """SPEC 067: `<archive_root>/vault-*.tar.gz.gpg` retention.

    SPEC 041.1 `prune_backups` kardeşi — glob `vault-*.tar.gz.gpg`.
    Semantik aynı: mtime desc + ilk `keep` tutar; gerisini siler.
    Plain `.tar.gz` dosyalarına DOKUNMAZ (SPEC 041.1 ayrı çalışır).

    - `keep < 1` → `VaultBackupError`.
    - `archive_root` yok → boş liste (cron nazikliği).
    - Silme hatası → `VaultBackupError`.
    """
    if keep < 1:
        raise VaultBackupError(f"keep >= 1 olmalı: {keep}")
    if not archive_root.is_dir():
        return []
    candidates = sorted(
        archive_root.glob("vault-*.tar.gz.gpg"),
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
            # SPEC 049: ortak güvenlik doğrulaması.
            # Mesaj metni SPEC 041 sözleşmesini korur.
            try:
                verify_tar_members(members, _ARCNAME)
            except UnsafeTarMemberError as exc:
                raise VaultBackupError(str(exc)) from exc
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

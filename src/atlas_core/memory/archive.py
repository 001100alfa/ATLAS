"""Arşiv: tamamlanan görev artefaktlarını soğuk depoya taşır.

Sıcak alan (pipeline/tasks/) küçük kalır; geçmiş kaybolmaz.
Arşivlenen görev vault'a özet notla bağlanır -> graf hatırlar.
"""
from __future__ import annotations

import shutil
import tarfile
from datetime import date
from pathlib import Path

from atlas_core.memory.vault import Vault
from atlas_core.utils.safe_tar import UnsafeTarMemberError, verify_tar_members


class RestoreError(RuntimeError):
    """SPEC 033: arşiv geri yükleme hatası (kullanıcıya yansıyacak)."""


def archive_task(task_dir: Path, archive_root: Path, vault: Vault, summary: str) -> Path:
    """Görev klasörünü tar.gz'e alır, özetini vault'a düğüm olarak yazar.

    Args:
        task_dir: pipeline/tasks/XXX klasörü.
        archive_root: arşiv kök dizini.
        vault: özet notunun yazılacağı beyin.
        summary: tek paragraf teslim özeti (SHIP raporundan).

    Returns:
        Oluşan arşiv dosyasının yolu.
    """
    if not task_dir.is_dir():
        raise FileNotFoundError(f"Görev klasörü yok: {task_dir}")
    archive_root.mkdir(parents=True, exist_ok=True)
    tar_path = archive_root / f"{task_dir.name}-{date.today().isoformat()}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(task_dir, arcname=task_dir.name)

    vault.write(
        f"task-{task_dir.name}",
        f"# Görev {task_dir.name}\n#arşiv\n\n{summary}\n\n"
        f"Arşiv: `{tar_path.name}`\nİlgili: [[DECISIONS]]\n",
        folder="tasks",
    )
    shutil.rmtree(task_dir)
    return tar_path


def _find_archive_for_task(archive_root: Path, task_id: str) -> Path | None:
    """SPEC 033: `<archive_root>/<task_id>-YYYY-MM-DD.tar.gz` desenlerinden
    mtime'ı en yeni olanı döner. Yoksa `None`.

    Bir görevin birden fazla arşiv sürümü olabilir (aynı id ile tekrar
    arşivlenmiş); geri yükleme her zaman en son sürüme yapılır.
    """
    if not archive_root.is_dir():
        return None
    candidates = sorted(
        archive_root.glob(f"{task_id}-*.tar.gz"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _is_within(base: Path, target: Path) -> bool:
    """Path traversal koruması: `target` `base` altında mı."""
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def restore_task(
    task_id: str, archive_root: Path, tasks_root: Path
) -> tuple[Path, Path]:
    """SPEC 033: `<task_id>` arşivini `<tasks_root>/<task_id>` altına aç.

    Args:
        task_id: `pipeline/tasks/` altında oluşacak klasör adı (arşivin
            tar kökündeki `arcname` ile aynı).
        archive_root: `.tar.gz` dosyalarının bulunduğu kök.
        tasks_root: Görevlerin geri açılacağı kök (`pipeline/tasks`).

    Returns:
        `(tar_path, restored_dir)` — kaynak arşiv ve geri yüklenen klasör.

    Raises:
        RestoreError:
            - `archive_root` yoksa
            - `<task_id>-*.tar.gz` yoksa
            - `<tasks_root>/<task_id>` ZATEN varsa (çakışma; --force yok)
            - tar üyesi yol dışına çıkıyorsa (path traversal)
            - I/O hatası (extract patlarsa)
    """
    if not archive_root.is_dir():
        raise RestoreError(f"arşiv kökü yok: {archive_root}")
    tar_path = _find_archive_for_task(archive_root, task_id)
    if tar_path is None:
        raise RestoreError(
            f"arşiv bulunamadı: {archive_root}/{task_id}-*.tar.gz"
        )
    restored_dir = tasks_root / task_id
    if restored_dir.exists():
        raise RestoreError(
            f"hedef zaten var: {restored_dir} (önce silin veya taşıyın)"
        )
    tasks_root.mkdir(parents=True, exist_ok=True)
    # SPEC 049: Path traversal + kolon + kök arcname kontrolü ortak
    # yardımcıya (`utils/safe_tar.py`). Mesaj metni korunur — mevcut
    # SPEC 033 test sözleşmesi (regex match) bit-uyumlu.
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            members = tar.getmembers()
            try:
                verify_tar_members(members, task_id)
            except UnsafeTarMemberError as exc:
                raise RestoreError(str(exc)) from exc
            # Python 3.12+ 'data' filter — symlink/absolute reddi.
            # Üyeler zaten `verify_tar_members` ile doğrulandı;
            # defense-in-depth ikinci kat.
            tar.extractall(tasks_root, filter="data")  # noqa: S202
    except (OSError, tarfile.TarError) as exc:
        # Yarım açılmış olabilir → temizle
        if restored_dir.exists():
            shutil.rmtree(restored_dir, ignore_errors=True)
        raise RestoreError(f"extract başarısız: {exc}") from exc

    if not _is_within(tasks_root, restored_dir):
        # Ekstra güvenlik ağı — normalde imkânsız (task_id kontrolü var)
        shutil.rmtree(restored_dir, ignore_errors=True)
        raise RestoreError(f"geri yüklenen yol tasks_root dışında: {restored_dir}")
    return tar_path, restored_dir

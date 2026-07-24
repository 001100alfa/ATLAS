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

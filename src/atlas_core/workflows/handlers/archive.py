"""`memory.archive` handler — tamamlanmış görevi archive_task() ile arşivler.

Varsayılan `dry_run=True` — YIKICI (shutil.rmtree) etkiyi yanlışlıkla
tetiklememek için. Gerçek arşivleme YAML'da `with: {dry_run: false}` ister.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from atlas_core.memory.archive import archive_task
from atlas_core.memory.vault import Vault
from atlas_core.workflows.handlers._errors import HandlerError

Handler = Callable[[dict[str, object]], str]


def make_archive_handler(
    tasks_root: Path | None = None,
    archive_root: Path | None = None,
    vault_root: Path | None = None,
    dry_run: bool = True,
) -> Handler:
    """`with: {task: 002-orkestrator-canlanma, summary?: ..., dry_run?: bool}`.

    Handler-düzeyi `dry_run` YAML-düzeyi `dry_run` tarafından geçersiz kılınır
    (YAML kazanır — kullanıcı niyeti önce).
    """
    tasks_root = tasks_root or Path("pipeline/tasks")
    archive_root = archive_root or Path("archive")
    vault_root = vault_root or Path("vault")

    def _archive(params: dict[str, object]) -> str:
        task_raw = params.get("task")
        if not isinstance(task_raw, str) or not task_raw:
            raise HandlerError("memory.archive: 'task' parametresi zorunlu (str)")
        yaml_dry = params.get("dry_run")
        effective_dry = yaml_dry if isinstance(yaml_dry, bool) else dry_run
        task_dir = tasks_root / task_raw
        if not task_dir.is_dir():
            raise HandlerError(f"memory.archive: görev klasörü yok: {task_dir}")
        summary_raw = params.get("summary")
        summary = summary_raw if isinstance(summary_raw, str) else f"{task_raw} arşivlendi"

        if effective_dry:
            return f"[dry-run] memory.archive: {task_dir} -> {archive_root}/"

        vault = Vault(vault_root)
        archive_path = archive_task(task_dir, archive_root, vault, summary)
        return f"arşivlendi: {archive_path}"

    return _archive

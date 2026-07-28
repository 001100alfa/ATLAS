"""Yerleşik handler'ları WorkflowEngine'e kaydeden fabrika.

Yeni handler eklerken:
1. `handlers/<isim>.py` yaz (`make_<isim>_handler() -> Handler`).
2. Aşağıya `engine.register("...", make_...())` satırı ekle.
3. Testini `tests/test_handlers_<isim>.py`'de ver.
"""

from __future__ import annotations

from pathlib import Path

from atlas_core.workflows.engine import WorkflowEngine
from atlas_core.workflows.handlers._errors import HandlerError
from atlas_core.workflows.handlers.archive import make_archive_handler
from atlas_core.workflows.handlers.gate import make_gate_handler
from atlas_core.workflows.handlers.test import make_test_handler

__all__ = ["HandlerError", "register_builtins"]


def register_builtins(
    engine: WorkflowEngine,
    *,
    dry_run: bool = False,
    tasks_root: Path | None = None,
    archive_root: Path | None = None,
    vault_root: Path | None = None,
) -> None:
    """Üç kanıt handler'ını kaydeder: pipeline.gate, pipeline.test, memory.archive.

    `dry_run=True` → subprocess/arşivleme atlanır, sadece raporlanır.
    """
    engine.register("pipeline.gate", make_gate_handler())
    engine.register("pipeline.test", make_test_handler(dry_run=dry_run))
    engine.register(
        "memory.archive",
        make_archive_handler(
            tasks_root=tasks_root,
            archive_root=archive_root,
            vault_root=vault_root,
            dry_run=dry_run,
        ),
    )

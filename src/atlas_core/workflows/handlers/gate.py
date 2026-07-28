"""`pipeline.gate` handler — belirli bir artefakt dosyasının varlığını doğrular."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from atlas_core.workflows.handlers._errors import HandlerError

Handler = Callable[[dict[str, object]], str]


def make_gate_handler() -> Handler:
    """Kullanım: `uses: pipeline.gate` + `with: {file: pipeline/tasks/002/02-spec.md}`."""

    def _gate(params: dict[str, object]) -> str:
        file_raw = params.get("file")
        if not isinstance(file_raw, str) or not file_raw:
            raise HandlerError("pipeline.gate: 'file' parametresi zorunlu (str)")
        path = Path(file_raw)
        if not path.is_file():
            raise HandlerError(f"pipeline.gate: dosya yok: {file_raw!r}")
        return f"gate GEÇTİ: {file_raw}"

    return _gate

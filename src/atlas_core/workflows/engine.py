"""Workflow motoru (gstack): YAML'da tanımlı adım yığınlarını yürütür.

Her adım kayıtlı bir handler'a bağlanır; bilinmeyen adım = hata
(sessiz atlama yok). Her adım audit'e işlenir.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

from atlas_core.security.audit import AuditLog

Handler = Callable[[dict[str, object]], str]


class WorkflowError(RuntimeError):
    """Workflow tanım veya yürütme hatası."""


@dataclass(frozen=True, slots=True)
class StepResult:
    step: str
    output: str


class WorkflowEngine:
    def __init__(self, audit: AuditLog) -> None:
        self._handlers: dict[str, Handler] = {}
        self._audit = audit

    def register(self, name: str, handler: Handler) -> None:
        self._handlers[name] = handler

    def run(self, yaml_path: Path) -> list[StepResult]:
        spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not isinstance(spec, dict) or "steps" not in spec:
            raise WorkflowError(f"Geçersiz workflow: {yaml_path}")
        results: list[StepResult] = []
        for raw in spec["steps"]:
            name = raw.get("uses")
            if name not in self._handlers:
                raise WorkflowError(f"Kayıtsız adım: {name!r}")
            out = self._handlers[name](raw.get("with", {}))
            self._audit.record("workflow", name, out[:200])
            results.append(StepResult(step=name, output=out))
        return results

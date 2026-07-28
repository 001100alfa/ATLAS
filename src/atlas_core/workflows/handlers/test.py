"""`pipeline.test` handler — pytest alt-kümesi çalıştırır, exit 0 zorunlu."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable

from atlas_core.workflows.handlers._errors import HandlerError

Handler = Callable[[dict[str, object]], str]

TEST_TIMEOUT_S: float = 300.0


def make_test_handler(dry_run: bool = False) -> Handler:
    """`with: {paths: [tests/goals]}` — varsayılan `[tests]`."""

    def _test(params: dict[str, object]) -> str:
        paths_raw = params.get("paths", ["tests"])
        if not isinstance(paths_raw, list) or not all(isinstance(p, str) for p in paths_raw):
            raise HandlerError("pipeline.test: 'paths' str listesi olmalı")
        cmd = [sys.executable, "-m", "pytest", "-q", *paths_raw]
        if dry_run:
            return f"[dry-run] pipeline.test: {' '.join(cmd)}"
        try:
            proc = subprocess.run(  # noqa: S603 — shell=False, arg listesi
                cmd,
                shell=False,
                capture_output=True,
                text=True,
                timeout=TEST_TIMEOUT_S,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            raise HandlerError(f"pipeline.test: timeout ({TEST_TIMEOUT_S}s)") from exc
        if proc.returncode != 0:
            tail = (proc.stdout or "")[-500:]
            raise HandlerError(f"pipeline.test: exit={proc.returncode}\n{tail}")
        # "N passed" satırından test sayısını çıkarma (best-effort).
        summary = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else "OK"
        return f"pytest OK: {summary}"

    return _test

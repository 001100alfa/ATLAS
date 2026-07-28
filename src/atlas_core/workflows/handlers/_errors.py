"""Workflow handler ortak tipleri."""

from __future__ import annotations


class HandlerError(RuntimeError):
    """Handler yürütme hatası — workflow durur, exit 6."""

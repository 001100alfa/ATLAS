"""Güvenlik katmanı: değiştirilemez denetim izi + sır tarayıcı.

Audit log append-only'dir; her kayıt bir önceki kaydın hash'ini taşır
(hash zinciri) -> geçmiş sessizce değiştirilemez.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

# Bilinen sır kalıpları (savunma amaçlı tespit)
SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9-]{20,}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "generic_assignment": re.compile(
        r"(?i)(password|passwd|secret|api_key|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]"
    ),
}


class AuditLog:
    """Hash-zincirli, sadece-ekle denetim günlüğü (JSONL)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return "GENESIS"
        lines = self.path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return "GENESIS"
        rec: dict[str, str] = json.loads(lines[-1])
        return rec["hash"]

    def record(self, actor: str, action: str, detail: str) -> dict[str, str]:
        """Olayı zincire ekler; kayıt sözlüğünü döndürür."""
        prev = self._last_hash()
        body = {
            "ts": datetime.now(UTC).isoformat(),
            "actor": actor,
            "action": action,
            "detail": detail,
            "prev": prev,
        }
        digest = hashlib.sha256(
            json.dumps(body, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        rec = {**body, "hash": digest}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def verify(self) -> bool:
        """Zincir bütünlüğünü doğrular; oynanmışsa False."""
        prev = "GENESIS"
        if not self.path.exists():
            return True
        for line in self.path.read_text(encoding="utf-8").strip().splitlines():
            rec: dict[str, str] = json.loads(line)
            body = {k: rec[k] for k in ("ts", "actor", "action", "detail", "prev")}
            if rec["prev"] != prev:
                return False
            digest = hashlib.sha256(
                json.dumps(body, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            if digest != rec["hash"]:
                return False
            prev = rec["hash"]
        return True


def scan_secrets(text: str) -> list[tuple[str, str]]:
    """Metinde sır kalıpları arar; (kalıp_adı, maskeli_eşleşme) döndürür."""
    hits: list[tuple[str, str]] = []
    for name, pat in SECRET_PATTERNS.items():
        for m in pat.finditer(text):
            s = m.group(0)
            hits.append((name, s[:6] + "…" + s[-4:] if len(s) > 12 else "***"))
    return hits

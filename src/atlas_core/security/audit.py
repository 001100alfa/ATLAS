"""Güvenlik katmanı: değiştirilemez denetim izi + sır tarayıcı.

Audit log append-only'dir; her kayıt bir önceki kaydın hash'ini taşır
(hash zinciri) -> geçmiş sessizce değiştirilemez.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import UTC, datetime
from pathlib import Path

# SPEC 031: Aynı audit dosyasına birden çok thread'in append yapması
# hash zincirini bozabilir (iki thread aynı prev hash'i okuyup farklı
# zincir noktalarına yazar). Dosya-path bazlı lock: aynı `path`
# üzerindeki AuditLog kayıtları serileşir.
_AUDIT_LOCKS: dict[str, threading.Lock] = {}
_AUDIT_LOCKS_MUTEX = threading.Lock()


def _lock_for(path: Path) -> threading.Lock:
    """SPEC 031: Path'e göre paylaşılan thread lock döner (module-scope)."""
    key = str(path.resolve())
    with _AUDIT_LOCKS_MUTEX:
        lock = _AUDIT_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _AUDIT_LOCKS[key] = lock
        return lock

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
        """Olayı zincire ekler; kayıt sözlüğünü döndürür.

        SPEC 031: Aynı dosyaya yazan tüm thread'ler `_lock_for(path)`
        üzerinde serileşir (hash zinciri race'ini engelle).
        """
        with _lock_for(self.path):
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
        """Zincir bütünlüğünü doğrular; oynanmışsa False.

        SPEC 031: Boş satırları atlar (paralel append arasında görülen
        yarım-satır artefaktları için fail-safe). JSON parse hatası ise
        zincir sözleşmesi bozulmuş demektir → False.
        """
        prev = "GENESIS"
        if not self.path.exists():
            return True
        with _lock_for(self.path):
            content = self.path.read_text(encoding="utf-8")
        for line in content.strip().splitlines():
            if not line.strip():
                continue  # SPEC 031: boş satır — sessiz skip
            try:
                rec: dict[str, str] = json.loads(line)
            except json.JSONDecodeError:
                return False
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

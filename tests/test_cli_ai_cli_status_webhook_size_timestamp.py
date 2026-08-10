"""SPEC 180 — ai-cli status --alert-webhook payload size_bytes + timestamp."""

from __future__ import annotations

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from atlas_core.cli import main


def _mkpkg(root: Path, deps: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps({"dependencies": deps}), encoding="utf-8",
    )


def _mkinstalled(root: Path, name: str, version: str, extra_bytes: int = 0) -> None:
    pkg_dir = root / "node_modules" / name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "package.json").write_text(
        json.dumps({"version": version}), encoding="utf-8",
    )
    if extra_bytes > 0:
        (pkg_dir / "blob.bin").write_bytes(b"x" * extra_bytes)


def _serve(status: int = 200, capture: list | None = None):
    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            if capture is not None:
                capture.append({"body": body.decode("utf-8")})
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_a, **_kw):  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)

    def _shutdown():
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
    return port, _shutdown


def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.chdir(tmp_path)


ISO_8601_SECONDS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def test_180_payload_size_bytes_alani(monkeypatch, tmp_path, capsys):
    """SPEC 180: payload'da `size_bytes` alanı var + doğru değer."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"opencode-ai": "^1.19.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "opencode-ai", "1.18.5",
                 extra_bytes=4096)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "ai-cli", "status", "opencode-ai",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert "size_bytes" in body
    assert isinstance(body["size_bytes"], int)
    assert body["size_bytes"] >= 4096  # blob + package.json'lar


def test_180_payload_timestamp_iso_8601(monkeypatch, tmp_path, capsys):
    """SPEC 180: payload.timestamp ISO 8601 seconds formatı."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"kimi": "^0.2.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "kimi", "0.1.0")
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "ai-cli", "status", "kimi",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    body = json.loads(capture[0]["body"])
    assert "timestamp" in body
    assert ISO_8601_SECONDS_RE.match(body["timestamp"]), \
        f"Beklenmedik timestamp formatı: {body['timestamp']!r}"


def test_180_mevcut_alanlar_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 170 mevcut 6 alan + SPEC 180 2 yeni alan = 8 alan."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"cline": "^3.0.47"})
    _mkinstalled(tmp_path / "tools/ai-cli", "cline", "3.0.40")
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "ai-cli", "status", "cline",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    body = json.loads(capture[0]["body"])
    # SPEC 170 mevcut 6 + SPEC 180 2 yeni = 8
    assert set(body.keys()) == {
        "alert", "name", "installed_version", "declared_version",
        "up_to_date", "install_dir",
        "size_bytes", "timestamp",
    }
    assert body["alert"] == "ai-cli-status"
    assert body["name"] == "cline"
    assert body["up_to_date"] is False


def test_180_up_to_date_true_post_yok(monkeypatch, tmp_path, capsys):
    """SPEC 170 bit-uyumlu: up_to_date=True → POST atılmaz (yeni alanlar
    da yok — POST hiç atılmıyor)."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"kilo": "^1.0.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "kilo", "1.0.0")
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "ai-cli", "status", "kilo",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []

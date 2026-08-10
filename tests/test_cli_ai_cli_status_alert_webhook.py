"""SPEC 170 — atlas ai-cli status --alert-webhook URL testleri."""

from __future__ import annotations

import json
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


def _mkinstalled(root: Path, name: str, version: str) -> None:
    pkg_dir = root / "node_modules" / name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "package.json").write_text(
        json.dumps({"version": version}), encoding="utf-8",
    )


def _serve(status: int = 200, capture: list | None = None):
    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            if capture is not None:
                capture.append({
                    "path": self.path,
                    "body": body.decode("utf-8"),
                    "content_type": self.headers.get("Content-Type"),
                })
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


def test_170_up_to_date_false_post_atilir(monkeypatch, tmp_path, capsys):
    """installed != declared → up_to_date=False → POST atılır."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"opencode-ai": "^1.19.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "opencode-ai", "1.18.5")
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
    assert body["alert"] == "ai-cli-status"
    assert body["name"] == "opencode-ai"
    assert body["installed_version"] == "1.18.5"
    assert body["declared_version"] == "^1.19.0"
    assert body["up_to_date"] is False
    assert "install_dir" in body
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarılı" in err


def test_170_up_to_date_true_post_atilmaz(monkeypatch, tmp_path, capsys):
    """up_to_date=True → POST atılmaz (sessiz)."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"cline": "^3.0.47"})
    _mkinstalled(tmp_path / "tools/ai-cli", "cline", "3.0.47")
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
    assert capture == []
    err = capsys.readouterr().err
    assert "[alert-webhook]" not in err


def test_170_post_basarisiz_exit_code_korur(monkeypatch, tmp_path, capsys):
    """POST 500 → başarısız stderr; exit code KORUR."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"kimi": "^0.2.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "kimi", "0.1.0")
    port, shutdown = _serve(status=500)
    try:
        rc = main([
            "ai-cli", "status", "kimi",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0  # exit code KORUR
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err
    assert "HTTP 500" in err


def test_170_schema_modda_webhook_yok(monkeypatch, tmp_path, capsys):
    """SPEC 146 --schema kısa devre --alert-webhook'u YOK sayar."""
    _env(monkeypatch, tmp_path)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "ai-cli", "status", "--schema",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []  # schema kısa devre → POST atılmaz


def test_170_url_scheme_gecersiz(monkeypatch, tmp_path, capsys):
    """SSRF savunma: file:// scheme → POST başarısız (exit code korur)."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"kilo": "^1.0.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "kilo", "0.9.0")
    rc = main([
        "ai-cli", "status", "kilo",
        "--alert-webhook", "file:///etc/passwd",
    ])
    assert rc == 0
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err


def test_170_ge_hersey_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--alert-webhook YOK → SPEC 037.4 davranışı AYNI."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"kimi": "^0.2.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "kimi", "0.1.0")
    rc = main(["ai-cli", "status", "kimi"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "kimi" in out
    assert "0.1.0" in out


def test_170_json_ciktisi_ile_ortogonal(monkeypatch, tmp_path, capsys):
    """--json çıktısı + --alert-webhook → stdout JSON, stderr uyarı."""
    _env(monkeypatch, tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"opencode-ai": "^1.19.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "opencode-ai", "1.18.5")
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "ai-cli", "status", "opencode-ai", "--json",
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert len(capture) == 1
    # stdout hâlâ JSON
    stdout = capsys.readouterr().out
    data = json.loads(stdout)
    assert data["up_to_date"] is False

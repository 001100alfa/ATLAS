"""SPEC 202 — ai-cli status --alert-webhook payload bin_path."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from atlas_core.cli import main


def _mkpkg(root: Path, deps: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(json.dumps({"dependencies": deps}))


def _mkinstalled(root: Path, name: str, version: str) -> None:
    d = root / "node_modules" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "package.json").write_text(json.dumps({"version": version}))


def _serve(cap: list):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            n = int(self.headers.get("Content-Length", "0"))
            cap.append(self.rfile.read(n).decode())
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_a, **_kw):  # noqa: A003
            return

    s = ThreadingHTTPServer(("127.0.0.1", 0), H)
    p = s.server_address[1]
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    time.sleep(0.05)

    def _stop():
        s.shutdown()
        s.server_close()
        t.join(timeout=2.0)
    return p, _stop


def test_202_bin_path_alani(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.chdir(tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"opencode-ai": "^1.19.0"})
    _mkinstalled(tmp_path / "tools/ai-cli", "opencode-ai", "1.18.5")
    cap: list = []
    port, sd = _serve(cap)
    try:
        rc = main(["ai-cli", "status", "opencode-ai",
                   "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    assert rc == 0
    body = json.loads(cap[0])
    assert "bin_path" in body


def test_202_alan_sayisi_9(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.chdir(tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"cline": "^3.0.47"})
    _mkinstalled(tmp_path / "tools/ai-cli", "cline", "3.0.40")
    cap: list = []
    port, sd = _serve(cap)
    try:
        main(["ai-cli", "status", "cline",
              "--alert-webhook", f"http://127.0.0.1:{port}/h"])
    finally:
        sd()
    body = json.loads(cap[0])
    # SPEC 170 6 + SPEC 180 2 + SPEC 202 1 = 9
    assert set(body.keys()) == {
        "alert", "name", "installed_version", "declared_version",
        "up_to_date", "install_dir",
        "size_bytes", "timestamp",
        "bin_path",
    }


def test_202_schema_alert_payload_bin_path(monkeypatch, tmp_path, capsys):
    """SPEC 194 alert_payload'a bin_path eklendi (9 alan)."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["ai-cli", "status", "--schema"])
    assert rc == 0
    d = json.loads(capsys.readouterr().out.strip())
    names = {f["name"] for f in d["alert_payload"]}
    assert "bin_path" in names
    by = {f["name"]: f for f in d["alert_payload"]}
    assert by["bin_path"]["spec"] == "202"

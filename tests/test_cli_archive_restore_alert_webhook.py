"""SPEC 176 — atlas archive --restore --alert-webhook URL testleri."""

from __future__ import annotations

import json
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    tasks = tmp_path / "tasks"
    arc = tmp_path / "arc"
    tasks.mkdir()
    arc.mkdir()
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)
    return tasks, arc


def _mktar(archive_root: Path, task_id: str, extra_file: str = "09-ship.md",
           content: str = "shipped") -> Path:
    """SPEC 007 kalıbı arşiv üret: <task>-YYYY-MM-DD.tar.gz."""
    from datetime import date
    tar_path = archive_root / f"{task_id}-{date.today().isoformat()}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        # tarball root dizin adı task_id
        data = content.encode()
        import io
        info = tarfile.TarInfo(name=f"{task_id}/{extra_file}")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return tar_path


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


def test_176_arsiv_bulunamadi_post_atilir(monkeypatch, tmp_path, capsys):
    """Arşiv bulunamadı (exit 6) → POST atılır."""
    tasks, arc = _env(monkeypatch, tmp_path)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "archive", "--restore", "yok-task-id", "--apply",
            "--tasks-root", str(tasks), "--archive-root", str(arc),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 6
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["alert"] == "archive-restore"
    assert body["task_id"] == "yok-task-id"
    assert body["exit_code"] == 6
    assert "bulunamadı" in body["error"]


def test_176_cakisma_exit_3_post_atilir(monkeypatch, tmp_path, capsys):
    """RestoreError çakışma (exit 3) → POST atılır."""
    tasks, arc = _env(monkeypatch, tmp_path)
    _mktar(arc, "task-x")
    (tasks / "task-x").mkdir()  # hedef zaten var
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "archive", "--restore", "task-x", "--apply",
            "--tasks-root", str(tasks), "--archive-root", str(arc),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 3
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["alert"] == "archive-restore"
    assert body["task_id"] == "task-x"
    assert body["exit_code"] == 3
    assert "zaten var" in body["error"]


def test_176_basarili_restore_post_atilmaz(monkeypatch, tmp_path, capsys):
    """Başarılı restore (exit 0) → POST atılmaz (sessiz)."""
    tasks, arc = _env(monkeypatch, tmp_path)
    _mktar(arc, "task-ok")
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "archive", "--restore", "task-ok", "--apply",
            "--tasks-root", str(tasks), "--archive-root", str(arc),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0
    assert capture == []
    err = capsys.readouterr().err
    assert "alert-webhook" not in err


def test_176_dry_run_post_atilmaz(monkeypatch, tmp_path, capsys):
    """Dry-run (--apply yok) → hedef var olsa da POST atılmaz."""
    tasks, arc = _env(monkeypatch, tmp_path)
    _mktar(arc, "task-y")
    (tasks / "task-y").mkdir()
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "archive", "--restore", "task-y",
            "--tasks-root", str(tasks), "--archive-root", str(arc),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 0  # dry-run başarılı
    assert capture == []  # POST atılmaz


def test_176_search_hic_eslesme_post_atilir(monkeypatch, tmp_path, capsys):
    """--search hiç eşleşme (exit 6) → POST atılır."""
    tasks, arc = _env(monkeypatch, tmp_path)
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "archive", "--restore", "--search", "xyz-not-there",
            "--tasks-root", str(tasks), "--archive-root", str(arc),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 6
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["search_pattern"] == "xyz-not-there"
    assert body["exit_code"] == 6
    assert body["task_id"] is None


def test_176_search_belirsiz_post_atilir(monkeypatch, tmp_path, capsys):
    """--search 2+ eşleşme (exit 2) → POST atılır."""
    tasks, arc = _env(monkeypatch, tmp_path)
    _mktar(arc, "alpha-task", extra_file="common.md")
    _mktar(arc, "beta-task", extra_file="common.md")
    capture: list = []
    port, shutdown = _serve(status=200, capture=capture)
    try:
        rc = main([
            "archive", "--restore", "--search", "common",
            "--tasks-root", str(tasks), "--archive-root", str(arc),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 2
    assert len(capture) == 1
    body = json.loads(capture[0]["body"])
    assert body["search_pattern"] == "common"
    assert body["exit_code"] == 2


def test_176_post_basarisiz_exit_code_korur(monkeypatch, tmp_path, capsys):
    """POST 500 → başarısız stderr; exit code KORUR (SPEC 064 kalıbı)."""
    tasks, arc = _env(monkeypatch, tmp_path)
    port, shutdown = _serve(status=500)
    try:
        rc = main([
            "archive", "--restore", "yok", "--apply",
            "--tasks-root", str(tasks), "--archive-root", str(arc),
            "--alert-webhook", f"http://127.0.0.1:{port}/hook",
        ])
    finally:
        shutdown()
    assert rc == 6  # exit code KORUR
    err = capsys.readouterr().err
    assert "[alert-webhook] POST başarısız" in err
    assert "HTTP 500" in err


def test_176_webhook_yok_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--alert-webhook YOK → SPEC 033 davranışı AYNI (exit code)."""
    tasks, arc = _env(monkeypatch, tmp_path)
    rc = main([
        "archive", "--restore", "yok", "--apply",
        "--tasks-root", str(tasks), "--archive-root", str(arc),
    ])
    assert rc == 6
    err = capsys.readouterr().err
    assert "ARŞİV HATASI" in err
    assert "alert-webhook" not in err

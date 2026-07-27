"""ATLAS Sağlık & Güncelleme Ajanı — yerel web sunucusu (yalnız stdlib).

`DOCTOR.cmd` bunu başlatır. Kurulum sihirbazıyla (`tools/setup_gui`) aynı
kalıbı izler: 127.0.0.1'e bağlanır, her istek oturum jetonu ister, arayüz tek
dosya HTML'dir.

API:
  GET  /                       arayüz
  GET  /api/steps              denetim adımlarının listesi
  POST /api/scan/<adım>        tek adımı çalıştır → bulgular
  POST /api/fix/<eylem>        anlık düzeltme
  POST /api/run/<eylem>        uzun düzeltme başlat → {"job": id}
  GET  /api/job/<id>           canlı çıktı
  POST /api/report             son taramadan Markdown rapor üret → dosya yolu
  POST /api/open               raporu/klasörü aç
"""

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from tools.setup_gui.connect import _strip_ansi
from tools.setup_gui.detect import project_root

from . import checks, fixes, report, versions

UI_DIR = Path(__file__).resolve().parent
ROOT = project_root()
TOKEN = secrets.token_urlsafe(24)

# Son taramanın bulguları — rapor üretimi buradan okur.
LAST: dict[str, list[dict]] = {}
LAST_LOCK = threading.Lock()


class Job:
    """Arka planda çalışan uzun düzeltme; çıktısı canlı okunur."""

    def __init__(self, jid: str, title: str, argv: list[str], cwd: Path):
        self.id = jid
        self.title = title
        self.argv = argv
        self.cwd = cwd
        self.lines: list[str] = []
        self.done = False
        self.code: int | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def _append(self, text: str) -> None:
        with self._lock:
            self.lines.append(text)
            del self.lines[:-400]

    def _run(self) -> None:
        self._append(f"$ {' '.join(self.argv)}")
        try:
            proc = subprocess.Popen(
                self.argv,
                cwd=str(self.cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as exc:
            self._append(f"[HATA] başlatılamadı: {exc}")
            self.code, self.done = 1, True
            return
        assert proc.stdout is not None
        for line in proc.stdout:
            self._append(_strip_ansi(line.rstrip()))
        self.code = proc.wait()
        self._append(f"[bitti] çıkış kodu {self.code}")
        self.done = True

    def snapshot(self, since: int = 0) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "title": self.title,
                "lines": self.lines[since:],
                "total": len(self.lines),
                "done": self.done,
                "code": self.code,
            }


JOBS: dict[str, Job] = {}


class Handler(BaseHTTPRequestHandler):
    server_version = "ATLASDoctor/1.0"

    def log_message(self, fmt: str, *args) -> None:
        pass

    # -- yardımcılar --
    def _json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path) -> None:
        if not path.is_file():
            self._json({"error": "bulunamadı"}, 404)
            return
        data = path.read_bytes()
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _authed(self, q: str) -> bool:
        given = (parse_qs(q).get("t") or [""])[0]
        return secrets.compare_digest(given, TOKEN)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    # -- yönlendirme --
    def do_GET(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        if u.path == "/":
            if not self._authed(u.query):
                self._json({"error": "gecersiz jeton — DOCTOR.cmd ile acin"}, 403)
                return
            self._file(UI_DIR / "ui.html")
            return
        if not self._authed(u.query):
            self._json({"error": "gecersiz jeton"}, 403)
            return

        if u.path == "/api/steps":
            self._json(
                {
                    "root": str(ROOT),
                    "steps": [{"id": s["id"], "label": s["label"]} for s in checks.STEPS],
                }
            )
            return

        if u.path.startswith("/api/job/"):
            job = JOBS.get(u.path.rsplit("/", 1)[-1])
            if not job:
                self._json({"error": "is bulunamadi"}, 404)
                return
            since = int((parse_qs(u.query).get("since") or ["0"])[0])
            self._json(job.snapshot(since))
            return

        self._json({"error": "bilinmeyen uc"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        if not self._authed(u.query):
            self._json({"error": "gecersiz jeton"}, 403)
            return
        path = u.path
        body = self._body()

        if path.startswith("/api/scan/"):
            step = path.rsplit("/", 1)[-1]
            if step == "_reset":  # yeni tarama: ağ önbelleğini boşalt
                versions.clear_cache()
                with LAST_LOCK:
                    LAST.clear()
                self._json({"ok": True})
                return
            findings = checks.run_step(step, ROOT, want_remote=bool(body.get("net", True)))
            # Arayüz düğmeye basmadan önce eylemin türünü bilmeli: anlık eylem
            # /api/fix, uzun kurulum işi /api/run uçlarına gider.
            for f in findings:
                act = f.get("fix")
                f["fix_kind"] = (
                    "instant"
                    if act in fixes.INSTANT
                    else ("job" if act and fixes.job_argv(act, ROOT) else None)
                )
                if act and not f["fix_kind"]:  # düzeltilemiyorsa düğme gösterme
                    f["fix"] = None
            with LAST_LOCK:
                LAST[step] = findings
            self._json({"step": step, "findings": findings, "summary": checks.summarize(findings)})
            return

        if path.startswith("/api/fix/"):
            action = path.rsplit("/", 1)[-1]
            if action not in fixes.INSTANT:
                self._json({"ok": False, "detail": f"bilinmeyen eylem: {action}"}, 400)
                return
            self._json(fixes.run_instant(action, ROOT, body))
            return

        if path.startswith("/api/run/"):
            action = path.rsplit("/", 1)[-1]
            spec = fixes.job_argv(action, ROOT)
            if not spec:
                self._json({"error": f"bu eylem calistirilamiyor: {action}"}, 400)
                return
            argv, title = spec
            jid = secrets.token_hex(6)
            job = Job(jid, title, argv, ROOT)
            JOBS[jid] = job
            job.start()
            self._json({"job": jid, "title": title})
            return

        if path == "/api/report":
            with LAST_LOCK:
                snapshot = {k: list(v) for k, v in LAST.items()}
            p = report.write_report(ROOT, snapshot)
            self._json({"ok": True, "path": str(p), "name": p.name})
            return

        if path == "/api/open":
            target = str(body.get("path") or "")
            p = Path(target)
            if not p.is_absolute():
                p = (ROOT / target).resolve()
            if ROOT not in p.parents and p != ROOT:
                self._json({"ok": False, "detail": "yol depo disinda"}, 400)
                return
            if not p.exists():
                self._json({"ok": False, "detail": "dosya yok"}, 404)
                return
            if os.name == "nt":
                os.startfile(str(p))  # noqa: S606 - kullanıcı isteğiyle dosya açma
            self._json({"ok": True})
            return

        self._json({"error": "bilinmeyen uc"}, 404)


def serve(port: int = 0, open_browser: bool = True) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/?t={TOKEN}"
    print("ATLAS Saglik & Guncelleme Ajani calisiyor.", flush=True)
    print(f"  Adres: {url}", flush=True)
    print("  Kapatmak icin bu pencerede Ctrl+C.", flush=True)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKapatiliyor...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    serve(port=int(os.environ.get("ATLAS_DOCTOR_PORT", "0")))

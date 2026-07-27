"""ATLAS kurulum sihirbazı — yerel web sunucusu (yalnız stdlib).

`SETUP.cmd` bunu başlatır: 127.0.0.1'de küçük bir HTTP sunucusu açar, arayüzü
tarayıcıda gösterir. Kullanıcının hiçbir şey kurması gerekmez — depoya gömülü
Python yeterlidir.

API:
  GET  /                     arayüz (tek dosya HTML)
  GET  /api/status           tam durum tespiti
  POST /api/probe            ajanları gerçekten test et (ACP el sıkışması)
  POST /api/run/<task>       uzun işi başlat → {"job": id}
  GET  /api/job/<id>         işin canlı çıktısı + bitiş durumu
  POST /api/register         ajanları acp.json'a yaz
  POST /api/keyless/<agent>  yerel Ollama'ya bağla (hesapsız)
  POST /api/auth/<agent>     kimlik akışını başlat (cihaz kodu / terminal)
  GET  /api/auth/<agent>     cihaz-kodu akışının durumu

Güvenlik: yalnız 127.0.0.1'e bağlanır ve her isteğin oturum jetonunu taşımasını
şart koşar; makinedeki başka bir uygulama arayüzü sürükleyemez.
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
from urllib.parse import urlparse

from . import connect as connect_mod
from .acp_probe import probe_all
from .detect import IS_WIN, LAUNCHERS, detect_all, project_root
from .install_ollama import MODEL_RE, start_server

UI_DIR = Path(__file__).resolve().parent
ROOT = project_root()
TOKEN = secrets.token_urlsafe(24)

# --- uzun işler -------------------------------------------------------------


class Job:
    """Arka planda çalışan bir kurulum adımı; çıktısı canlı okunur."""

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
            del self.lines[:-400]  # arayüz son satırları gösterir; bellek şişmesin

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
            self._append(connect_mod._strip_ansi(line.rstrip()))
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
LOGINS: dict[str, connect_mod.DeviceLogin] = {}


def _cmd(name: str, params: dict | None = None) -> list[str] | None:
    """Sihirbazın çalıştırabileceği kurulum görevleri."""
    params = params or {}

    # Yerel model sunucusu: kendi Python modülümüz (script değil).
    if name == "install-ollama":
        model = str(params.get("model") or "llama3.2:3b")
        if not MODEL_RE.match(model):  # kabuk yok ama yine de dar tutuyoruz
            return None
        return [sys.executable, "-X", "utf8", "-m", "tools.setup_gui.install_ollama",
                "--model", model]

    tasks = {
        # Çekirdek: çevrimdışı taşınabilir kurulum (vendor/wheels'ten).
        "install-core": [str(ROOT / "setup-portable.cmd")],
        # AI CLI'lar: npm + pip + goose ikilisi (internet gerekir).
        "install-clis": [str(ROOT / "setup-ai-cli.cmd")],
    }
    argv = tasks.get(name)
    if not argv or not Path(argv[0]).is_file():
        return None
    # .cmd dosyaları cmd.exe ile çalışır; kabuk enjeksiyonu olmasın diye argv listesi.
    return ["cmd.exe", "/c", *argv] if IS_WIN else argv


# --- HTTP -------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    server_version = "ATLASSetup/1.0"

    def log_message(self, fmt: str, *args) -> None:  # konsolu sessiz tut
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
        """Oturum jetonu doğrulaması (sabit süreli karşılaştırma)."""
        from urllib.parse import parse_qs

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
    def do_GET(self) -> None:  # noqa: N802 (stdlib arayüzü)
        u = urlparse(self.path)
        path, q = u.path, u.query

        if path == "/":
            if not self._authed(q):
                self._json({"error": "gecersiz jeton — SETUP.cmd ile acin"}, 403)
                return
            self._file(UI_DIR / "ui.html")
            return

        if not self._authed(q):
            self._json({"error": "gecersiz jeton"}, 403)
            return

        if path == "/api/status":
            self._json(detect_all(ROOT))
            return

        if path.startswith("/api/job/"):
            job = JOBS.get(path.rsplit("/", 1)[-1])
            if not job:
                self._json({"error": "is bulunamadi"}, 404)
                return
            from urllib.parse import parse_qs

            since = int((parse_qs(q).get("since") or ["0"])[0])
            self._json(job.snapshot(since))
            return

        if path.startswith("/api/auth/"):
            login = LOGINS.get(path.rsplit("/", 1)[-1])
            self._json(login.status() if login else {"error": "akis yok"})
            return

        self._json({"error": "bilinmeyen uc"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        path = u.path
        if not self._authed(u.query):
            self._json({"error": "gecersiz jeton"}, 403)
            return

        if path == "/api/probe":
            names = self._body().get("agents")
            self._json({"results": probe_all(ROOT, names)})
            return

        if path == "/api/register":
            self._json(connect_mod.register_agents(ROOT))
            return

        if path.startswith("/api/keyless/"):
            self._json(connect_mod.enable_keyless(path.rsplit("/", 1)[-1], ROOT))
            return

        if path.startswith("/api/auth/"):
            agent = path.rsplit("/", 1)[-1]
            mode = self._body().get("mode", "auto")
            spec_device = connect_mod.auth_command(agent, ROOT).get("device_flow")
            if mode == "terminal" or not spec_device:
                self._json(connect_mod.open_auth_terminal(agent, ROOT))
                return
            login = connect_mod.DeviceLogin(agent, ROOT)
            try:
                login.start()
            except OSError as exc:
                self._json({"ok": False, "detail": str(exc)})
                return
            LOGINS[agent] = login
            self._json({"ok": True, "started": True, "agent": agent})
            return

        if path == "/api/launch":
            # Beyaz liste: arayüzden gelen ad yalnız LAUNCHERS'taki betiğe eşlenir,
            # rastgele komut çalıştırılamaz.
            what = str(self._body().get("what") or "")
            spec = LAUNCHERS.get(what)
            if not spec:
                self._json({"ok": False, "detail": "bilinmeyen calistirma hedefi"}, 400)
                return
            script = ROOT / spec["script"]
            missing = [n for n in spec["needs"] if not (ROOT / n).is_file()]
            if not script.is_file() or missing:
                self._json(
                    {"ok": False, "detail": f"eksik: {', '.join(missing or [spec['script']])}"}
                )
                return
            try:
                if IS_WIN:
                    # Cift tiklamayla ayni davranis: kendi konsol/penceresinde acilir.
                    os.startfile(str(script))  # noqa: S606 - beyaz listeli, kullanıcı isteğiyle
                else:
                    subprocess.Popen([str(script)], cwd=str(ROOT), start_new_session=True)
            except OSError as exc:
                self._json({"ok": False, "detail": str(exc)})
                return
            self._json(
                {
                    "ok": True,
                    "detail": f"{spec['label']} baslatildi.",
                    "script": spec["script"],
                }
            )
            return

        if path == "/api/ollama/start":
            # Kurulu ama çalışmayan yerel model sunucusunu ayağa kaldırır.
            ok = start_server(ROOT)
            self._json(
                {
                    "ok": ok,
                    "detail": "Yerel model sunucusu calisiyor."
                    if ok
                    else "Sunucu baslatilamadi (kurulu mu?).",
                }
            )
            return

        if path.startswith("/api/run/"):
            name = path.rsplit("/", 1)[-1]
            argv = _cmd(name, self._body())
            if not argv:
                self._json({"error": f"gorev yok veya gecersiz parametre: {name}"}, 400)
                return
            jid = secrets.token_hex(6)
            job = Job(jid, name, argv, ROOT)
            JOBS[jid] = job
            job.start()
            self._json({"job": jid})
            return

        if path == "/api/open":
            target = self._body().get("path", "")
            p = (ROOT / target).resolve()
            if ROOT not in p.parents and p != ROOT:  # depo dışına çıkma
                self._json({"ok": False, "detail": "yol depo disinda"}, 400)
                return
            if IS_WIN:
                os.startfile(str(p))  # noqa: S606 - kullanıcı isteğiyle klasör açma
            self._json({"ok": True})
            return

        self._json({"error": "bilinmeyen uc"}, 404)


def serve(port: int = 0, open_browser: bool = True) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    actual = httpd.server_address[1]
    url = f"http://127.0.0.1:{actual}/?t={TOKEN}"
    # flush: cikti bir dosyaya yonlendirildiginde tamponda kalmasin — kullanici
    # adresi hemen gormeli.
    print("ATLAS Kurulum Sihirbazi calisiyor.", flush=True)
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
    serve(port=int(os.environ.get("ATLAS_SETUP_PORT", "0")))

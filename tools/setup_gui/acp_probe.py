"""ACP ajanlarını gerçekten deneyen bağlantı testi (yalnız stdlib).

Sihirbazın "Test et" düğmesi bunu çağırır. Kurulu olmak yetmez — ajan ancak
`initialize` + `session/new` el sıkışmasını geçerse panelde kullanılabilir.
Buradaki akış, Juggler'ın ACP istemcisiyle aynıdır (kabuksuz spawn, satır
sonlu JSON-RPC, aynı iki çağrı), böylece sonuç panelde göreceğinizle örtüşür.

Dönen durumlar:
  ready           — session/new başarılı, ajan kullanıma hazır
  needs_auth      — kimlik doğrulama gerekiyor (kullanıcı login yapmalı)
  needs_provider  — model sağlayıcı ayarlı değil (ör. goose GOOSE_PROVIDER)
  not_installed   — ikili/giriş dosyası yok
  error / timeout — diğer hatalar
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path

from .detect import acp_config_paths, acp_entry, agent_specs

ACP_PROTOCOL_VERSION = 1


def effective_entry(name: str, spec: dict, root: Path | None = None) -> dict:
    """Ajanın GERÇEKTE çalıştırılacak komut/args/env'i.

    Juggler kayıtlı `acp.json` girdisini kullanır (proje global'i ezer), spec'i
    değil. Test de aynısını kullanmalı — yoksa kayda yazılan env (ör. goose'un
    GOOSE_PROVIDER'ı) denenmemiş olur ve sonuç panelle örtüşmez.
    """
    for scope in ("project", "global"):  # proje önceliklidir
        path = acp_config_paths(root).get(scope)
        if not path or not path.is_file():
            continue
        try:
            agents = (json.loads(path.read_text(encoding="utf-8")) or {}).get("acpAgents") or {}
        except (OSError, json.JSONDecodeError):
            continue
        entry = agents.get(name)
        if isinstance(entry, dict) and entry.get("command"):
            return {
                "command": entry["command"],
                "args": list(entry.get("args") or []),
                "env": dict(entry.get("env") or {}),
            }
    return acp_entry(name, spec)  # henüz kayıtlı değil: spec'ten türet


def _classify(message: str, data: str = "") -> str:
    """Ajanın döndürdüğü hatayı kullanıcıya anlamlı bir duruma çevirir."""
    blob = f"{message} {data}".lower()
    if "auth" in blob:  # "Authentication required", "Call authenticate", ...
        return "needs_auth"
    if "provider" in blob or "api key" in blob or "api_key" in blob:
        return "needs_provider"
    return "error"


def probe_agent(name: str, root: Path | None = None, timeout: float = 50.0) -> dict:
    # 50 sn: kimi (Python CLI) soğuk başlangıçta ~20-30 sn alabiliyor ve testler
    # paralel koştuğunda yavaşlıyor; daha kısa süre yanlışlıkla "timeout" der.
    """Tek bir ajanı başlatıp el sıkışmayı dener ve durumunu döndürür."""
    specs = agent_specs(root)
    spec = specs.get(name)
    if spec is None:
        return {"name": name, "status": "error", "detail": f"bilinmeyen ajan: {name}"}

    if not Path(spec["bin"]).is_file():
        return {
            "name": name,
            "status": "not_installed",
            "detail": "kurulu değil — önce 'AI CLI kur' adımını çalıştırın",
        }

    entry = effective_entry(name, spec, root)
    env = {**os.environ, **entry["env"]}

    try:
        proc = subprocess.Popen(
            [entry["command"], *entry["args"]],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=str(root or Path(entry["command"]).anchor or Path.cwd()),
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False,  # Juggler de kabuk kullanmaz
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError as exc:
        return {"name": name, "status": "error", "detail": f"başlatılamadı: {exc}"}

    # stderr'i boşalt — dolu boru ajanı kilitler (stderr protokol değildir).
    stderr_tail: list[str] = []

    def drain() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            stderr_tail.append(line.rstrip())
            del stderr_tail[:-20]

    threading.Thread(target=drain, daemon=True).start()

    result: dict = {"name": name, "status": "timeout", "detail": "ajan yanıt vermedi"}

    def talk() -> None:
        nonlocal result
        assert proc.stdin is not None and proc.stdout is not None
        send = lambda obj: (  # noqa: E731 - kısa yardımcı
            proc.stdin.write(json.dumps(obj) + "\n"),
            proc.stdin.flush(),
        )
        try:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": ACP_PROTOCOL_VERSION,
                        "clientCapabilities": {},
                    },
                }
            )
            sent_new = False
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue  # ajanın gürültüsü; protokol değil
                if msg.get("method"):
                    continue  # ajanın bize sorduğu istek/bildirim — testte gereksiz
                mid, err = msg.get("id"), msg.get("error")
                if err:
                    result = {
                        "name": name,
                        "status": _classify(str(err.get("message", "")), str(err.get("data", ""))),
                        "detail": str(err.get("message", "")).strip() or "bilinmeyen hata",
                        "stage": "session/new" if mid == 1 else "initialize",
                    }
                    return
                if "result" in msg:
                    if mid == 0 and not sent_new:
                        sent_new = True
                        send(
                            {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "session/new",
                                # Ajan bu dizinde çalışacak; ileri slash Windows'ta da geçerli.
                                "params": {
                                    "cwd": str(root or Path.cwd()).replace("\\", "/"),
                                    "mcpServers": [],
                                },
                            }
                        )
                        continue
                    if mid == 1:
                        info = (msg.get("result") or {}).get("agentInfo") or {}
                        result = {
                            "name": name,
                            "status": "ready",
                            "detail": "bağlantı doğrulandı",
                            "version": info.get("version"),
                        }
                        return
        except (OSError, ValueError) as exc:
            result = {"name": name, "status": "error", "detail": str(exc)}

    worker = threading.Thread(target=talk, daemon=True)
    worker.start()
    worker.join(timeout)

    try:
        proc.kill()
    except OSError:
        pass

    if result["status"] in ("error", "timeout") and stderr_tail:
        result["stderr"] = "\n".join(stderr_tail[-6:])
    return result


def probe_all(root: Path | None = None, names: list[str] | None = None) -> list[dict]:
    """Ajanları paralel dener (her biri ayrı süreç; sıralı beklemek yavaş olur)."""
    names = names or list(agent_specs(root))
    out: dict[str, dict] = {}
    threads = []
    for n in names:
        t = threading.Thread(
            target=lambda x=n: out.__setitem__(x, probe_agent(x, root)), daemon=True
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join(70)  # probe_agent kendi timeout'unu (50 sn) uygular; bu üst sınır
    missing = {"status": "timeout", "detail": "test tamamlanmadı"}
    return [out.get(n, {"name": n, **missing}) for n in names]

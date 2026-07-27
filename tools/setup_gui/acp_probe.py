"""ACP ajanlarını gerçekten deneyen bağlantı testi (yalnız stdlib).

Sihirbazın "Test et" düğmesi bunu çağırır. Kurulu olmak yetmez — ajan ancak
el sıkışmayı geçerse panelde kullanılabilir. Buradaki akış, Juggler'ın ACP
istemcisiyle AYNIDIR (kabuksuz spawn, satır sonlu JSON-RPC, aynı çağrı sırası),
böylece sonuç panelde göreceğinizle örtüşür:

    initialize → session/new
                   └─ kimlik hatası verirse: authenticate(<ilan edilen yöntem>)
                      → session/new (bir kez yineleme)

Bu ikinci tur şart: cline gibi ajanlar CLI'dan giriş yapılmış olsa bile her
oturumu ACP `authenticate` çağrısına bağlar. Tur atlanırsa sınama "kimlik
gerekli" der ama panel aynı ajanı sorunsuz açar — yani sonuç YANILTICI olur.

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

# JSON-RPC istek numaraları. Ayrı sabitler, çünkü akış artık düz değil:
# initialize → session/new → (gerekirse) authenticate → session/new (yineleme).
ID_INIT, ID_NEW, ID_AUTH, ID_RETRY = 0, 1, 2, 3


def _auth_method_ids(init_result: dict) -> list[str]:
    """initialize yanıtındaki `authMethods` listesinden yöntem kimlikleri.

    Ajan hangi girişleri kabul ettiğini burada ilan eder (ör. cline: "cline",
    "openai-codex"). Panel `session/new` kimlik hatası verdiğinde bunları sırayla
    dener; CLI'dan giriş yapılmışsa authenticate etkileşimsiz geçer.
    """
    methods = init_result.get("authMethods")
    if not isinstance(methods, list):
        return []
    out: list[str] = []
    for m in methods:
        mid = m.get("id") if isinstance(m, dict) else m
        if isinstance(mid, str) and mid:
            out.append(mid)
    return out


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
    # session/new'in İLK hatası; authenticate denendikten sonra yanıt gelmezse
    # kullanıcıya bildirilecek asıl neden budur (bkz. fonksiyon sonu).
    first_error: dict | None = None

    def talk() -> None:
        nonlocal result, first_error
        assert proc.stdin is not None and proc.stdout is not None
        send = lambda obj: (  # noqa: E731 - kısa yardımcı
            proc.stdin.write(json.dumps(obj) + "\n"),
            proc.stdin.flush(),
        )
        try:
            new_session = {
                "jsonrpc": "2.0",
                "id": ID_NEW,
                "method": "session/new",
                # Ajan bu dizinde çalışacak; ileri slash Windows'ta da geçerli.
                "params": {
                    "cwd": str(root or Path.cwd()).replace("\\", "/"),
                    "mcpServers": [],
                },
            }
            send(
                {
                    "jsonrpc": "2.0",
                    "id": ID_INIT,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": ACP_PROTOCOL_VERSION,
                        "clientCapabilities": {},
                    },
                }
            )
            sent_new = False
            pending_methods: list[str] = []  # denenmemiş authenticate yöntemleri

            def try_authenticate() -> bool:
                """Sıradaki yöntemle authenticate dener. Yöntem kalmadıysa False."""
                while pending_methods:
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": ID_AUTH,
                            "method": "authenticate",
                            "params": {"methodId": pending_methods.pop(0)},
                        }
                    )
                    return True
                return False

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
                    detail = str(err.get("message", "")).strip() or "bilinmeyen hata"
                    status = _classify(detail, str(err.get("data", "")))
                    stage = {ID_INIT: "initialize", ID_AUTH: "authenticate"}.get(mid, "session/new")
                    failure = {"name": name, "status": status, "detail": detail, "stage": stage}
                    # session/new kimlik istiyorsa panel gibi davran: ilan edilen
                    # yöntemlerle authenticate et, session/new'i bir kez yinele.
                    if mid in (ID_NEW, ID_RETRY, ID_AUTH) and pending_methods:
                        first_error = first_error or failure
                        if try_authenticate():
                            continue
                    result = first_error or failure
                    return

                if "result" in msg:
                    if mid == ID_INIT and not sent_new:
                        sent_new = True
                        pending_methods = _auth_method_ids(msg.get("result") or {})
                        send(new_session)
                        continue
                    if mid == ID_AUTH:
                        # Kimlik kabul edildi; oturumu yeniden dene.
                        send({**new_session, "id": ID_RETRY})
                        continue
                    if mid in (ID_NEW, ID_RETRY):
                        info = (msg.get("result") or {}).get("agentInfo") or {}
                        result = {
                            "name": name,
                            "status": "ready",
                            "detail": "bağlantı doğrulandı"
                            + (" (authenticate sonrası)" if mid == ID_RETRY else ""),
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

    # authenticate'e girildiyse ve yanıt gelmediyse "timeout" yanıltıcıdır: ajan
    # kimlik olmadığı için orada etkileşim bekleyip asılmıştır. Asıl nedeni bildir.
    if result["status"] == "timeout" and first_error:
        result = {
            **first_error,
            "detail": first_error["detail"] + " (authenticate denendi, ajan yanıt vermedi)",
        }
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

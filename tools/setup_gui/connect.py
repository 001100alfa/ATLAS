"""Ajanları bağlama eylemleri: kayıt, anahtarsız yerel AI, kimlik akışları.

Sihirbazın "Bağlan" düğmelerinin arkasındaki iş. Üç ayrı sorunu çözer:

1. KAYIT       — ajanları `<proje>/.juggler/acp.json`'a yazar (Juggler bunu okur).
2. ANAHTARSIZ  — goose/kimi'yi yerel Ollama'ya bağlar; hesap/anahtar gerekmez.
3. KİMLİK      — hesap gerektiren ajanlar için doğru komutu gerçek bir terminalde
                 başlatır (cline'da cihaz-kodu URL'sini yakalayıp arayüze taşır).

Kimlik bilgisi ASLA burada işlenmez; giriş her zaman kullanıcının kendi
tarayıcısında/terminalinde olur.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

from . import wrappers
from .detect import IS_WIN, acp_config_paths, acp_entry, agent_specs, detect_ollama

# Araç çağırabilen (ACP ajanlarının ihtiyacı olan) modelleri öne alan tercih sırası.
MODEL_PREFERENCE = ("qwen2.5-coder", "llama3.1", "qwen3", "llama3", "mistral", "gemma")


# --- yerel AI arka ucu ------------------------------------------------------


def ollama_base_url(root: Path | None = None) -> str | None:
    """Konuşan bir Ollama varsa taban URL'si (önce proje portu, sonra sistem)."""
    info = detect_ollama(root)
    if info["port_serving"]:
        return f"http://127.0.0.1:{info['port']}"
    if info["system_running"]:
        return "http://127.0.0.1:11434"
    return None


def ollama_models(base_url: str, timeout: float = 5.0) -> list[str]:
    """Sunucudaki modelleri listeler (yoksa boş liste)."""
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=timeout) as resp:
            doc = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in doc.get("models", []) if m.get("name")]
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return []


def pick_model(models: list[str]) -> str | None:
    """Araç kullanımına en uygun modeli seçer; yoksa ilk modeli."""
    for wanted in MODEL_PREFERENCE:
        for m in models:
            if m.startswith(wanted):
                return m
    return models[0] if models else None


# --- 1) kayıt ---------------------------------------------------------------


def register_agents(
    root: Path | None = None, only_installed: bool = True, use_wrappers: bool = True
) -> dict:
    """Kurulu ajanları proje acp.json'ına yazar; mevcut girdileri korur.

    `use_wrappers` (varsayılan): `tools/agents/<ajan>.cmd` üretilir ve kayıt bunu
    gösterir. Ortam sarmalayıcıda toplanır, goose yerel modeli kendi başlatır ve
    `%APPDATA%` sızıntısı kapanır (bkz. wrappers.py). Kapatılırsa ikili doğrudan
    çağrılır ve ortam kayda gömülür (eski davranış).
    """
    root = root or Path.cwd()
    specs = agent_specs(root)
    path = acp_config_paths(root)["project"]
    path.parent.mkdir(parents=True, exist_ok=True)

    wrapper_result = wrappers.generate(root) if use_wrappers else {"ok": False}
    wrapped = set(wrapper_result.get("written") or [])

    doc: dict = {}
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}  # bozuk dosya: yeniden yazılır
    agents = dict(doc.get("acpAgents") or {})

    written, skipped = [], []
    for name, spec in specs.items():
        if only_installed and not Path(spec["bin"]).is_file():
            skipped.append(name)
            continue
        if name in wrapped:
            entry = wrappers.wrapper_entry(root, name, spec)
        else:
            entry = acp_entry(name, spec)
            # Daha önce yazılmış anahtarsız env'i (ör. goose) koru.
            prev_env = (agents.get(name) or {}).get("env") or {}
            for k, v in prev_env.items():
                entry["env"].setdefault(k, v)
        agents[name] = entry
        written.append(name)

    doc["acpAgents"] = agents
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "path": str(path),
        "written": written,
        "skipped": skipped,
        "wrapped": sorted(wrapped),
    }


# --- 2) anahtarsız yerel AI -------------------------------------------------


def enable_keyless(agent: str, root: Path | None = None) -> dict:
    """goose/kimi'yi yerel Ollama'ya bağlar (hesap/anahtar gerekmez)."""
    root = root or Path.cwd()
    base = ollama_base_url(root)
    if not base:
        return {
            "ok": False,
            "detail": "Çalışan bir Ollama bulunamadı. Önce 'Yerel AI' adımını tamamlayın.",
        }
    model = pick_model(ollama_models(base))
    if not model:
        return {
            "ok": False,
            "detail": f"{base} yanıt veriyor ama hiç model yok (ollama pull gerekli).",
        }

    if agent == "goose":
        return _keyless_goose(root, base, model)
    if agent == "kimi":
        # Yerel model yazılır ama ACP kapısı yine hesap ister (ölçüldü) — bunu
        # gizlemeyip söylüyoruz; sihirbaz kimi için "Giriş yap" yolunu önerir.
        res = _keyless_kimi(root, base, model)
        res["caveat"] = (
            "Yerel model doğrudan `kimi` kullanımında geçerli, ancak ACP/panel "
            "bağlantısı Kimi hesabı ister (kimi login)."
        )
        return res
    return {"ok": False, "detail": f"{agent} için anahtarsız mod yok (hesap gerekiyor)."}


def _keyless_goose(root: Path, base: str, model: str) -> dict:
    """goose'u yerel modele bağlar.

    Sarmalayıcı kullanılıyorsa seçim `tools/agents/local-model.cmd`'ye yazılır
    (sarmalayıcı onu `call` eder). Aksi hâlde env doğrudan acp.json kaydına
    gömülür — Juggler config env'ini üst süreç env'inin üstüne bindirir.
    """
    # Sarmalayıcı varsa model seçimi oraya gider; sarmalayıcı sabit kalır.
    if wrappers.wrapper_path(root, "goose").is_file():
        wrappers.write_local_model(root, base, model)
        return {"ok": True, "detail": f"goose → yerel Ollama ({model})", "model": model}

    path = acp_config_paths(root)["project"]
    doc = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    agents = doc.get("acpAgents") or {}
    if "goose" not in agents:
        reg = register_agents(root)
        if "goose" not in reg["written"]:
            return {"ok": False, "detail": "goose kurulu değil."}
        doc = json.loads(path.read_text(encoding="utf-8"))
        agents = doc["acpAgents"]

    agents["goose"].setdefault("env", {}).update(
        {"GOOSE_PROVIDER": "ollama", "GOOSE_MODEL": model, "OLLAMA_HOST": base}
    )
    doc["acpAgents"] = agents
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "detail": f"goose → yerel Ollama ({model})", "model": model}


def _keyless_kimi(root: Path, base: str, model: str) -> dict:
    """kimi'nin proje-yerel evine OpenAI-uyumlu Ollama sağlayıcısı yazar.

    ATLAS pip paketi `kimi-cli` kullanır (Juggler'daki npm `kimi-code` değil):
    config `$HOME/.kimi/config.toml`, OpenAI-uyumlu sağlayıcı tipi
    `openai_legacy`. Ajanın HOME'u spec tarafından proje-yerele çevrilir.
    """
    home = root / "tools" / "ai-cli" / "home" / "kimi-home"
    cfg_dir = home / ".kimi"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    alias = f"ollama/{model}"
    (cfg_dir / "config.toml").write_text(
        "# ATLAS kurulum sihirbazı tarafından yazıldı — anahtarsız yerel kurulum.\n"
        "# Kimi'yi yerel Ollama'ya (OpenAI-uyumlu uç) bağlar; hesap gerekmez.\n"
        "# Bulut Kimi hesabına dönmek için: kimi login (bu dosyayı günceller).\n"
        f'default_model = "{alias}"\n\n'
        "[providers.ollama]\n"
        'type = "openai_legacy"\n'
        # Ollama kimlik doğrulamaz; alan zorunlu olduğu için kısa bir yer tutucu.
        # (Gerçek bir sır değil — kasıtlı olarak kısa tutuldu ki sır taramasında
        # yanlış pozitif üretmesin.)
        'api_key = "none"\n'
        f'base_url = "{base}/v1"\n\n'
        f'[models."{alias}"]\n'
        'provider = "ollama"\n'
        f'model = "{model}"\n'
        "max_context_size = 131072\n"
        f'display_name = "{model} (yerel)"\n',
        encoding="utf-8",
    )
    return {"ok": True, "detail": f"kimi → yerel Ollama ({model})", "model": model}


# --- 3) kimlik akışları -----------------------------------------------------

# cline'ın bastığı cihaz-kodu satırlarını yakalar.
_URL_RE = re.compile(r"https?://\S+")
_CODE_RE = re.compile(r"\b([A-Z0-9]{4}-[A-Z0-9]{4})\b")


class DeviceLogin:
    """cline'ın cihaz-kodu akışını arka planda yürütür, URL/kodu arayüze verir."""

    def __init__(self, agent: str, root: Path):
        self.agent = agent
        self.root = root
        self.url: str | None = None
        self.code: str | None = None
        self.lines: list[str] = []
        self.done = False
        self.ok: bool | None = None
        self._proc: subprocess.Popen | None = None

    def start(self) -> None:
        spec = agent_specs(self.root)[self.agent]
        entry = acp_entry(self.agent, spec)
        auth_args = spec.get("auth_cmd") or ["auth"]
        # ACP argümanlarını at, kimlik argümanlarını koy.
        args = [a for a in entry["args"] if a not in spec["args"]] + list(auth_args)
        env = {**os.environ, **entry["env"]}
        self._proc = subprocess.Popen(
            [entry["command"], *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=str(self.root),
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        for raw in self._proc.stdout:
            line = _strip_ansi(raw.rstrip())
            if not line:
                continue
            self.lines.append(line)
            del self.lines[:-40]
            if self.url is None and (m := _URL_RE.search(line)):
                self.url = m.group(0)
            if self.code is None and (m := _CODE_RE.search(line)):
                self.code = m.group(1)
        rc = self._proc.wait()
        self.ok = rc == 0
        self.done = True

    def status(self) -> dict:
        return {
            "agent": self.agent,
            "url": self.url,
            "code": self.code,
            "done": self.done,
            "ok": self.ok,
            "log": self.lines[-12:],
        }

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.kill()


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


def auth_command(agent: str, root: Path | None = None) -> dict:
    """Ajanın kimlik komutunu, kullanıcının terminalde çalıştırabileceği biçimde."""
    root = root or Path.cwd()
    spec = agent_specs(root).get(agent)
    if not spec:
        return {"ok": False, "detail": f"bilinmeyen ajan: {agent}"}
    entry = acp_entry(agent, spec)
    auth_args = spec.get("auth_cmd") or ["auth"]
    args = [a for a in entry["args"] if a not in spec["args"]] + list(auth_args)
    parts = [entry["command"], *args]
    return {
        "ok": True,
        "command": " ".join(f'"{p}"' if " " in p else p for p in parts),
        "env": entry["env"],
        "device_flow": bool(spec.get("auth_device_flow")),
    }


def open_auth_terminal(agent: str, root: Path | None = None) -> dict:
    """Kimlik komutunu GERÇEK bir konsol penceresinde başlatır.

    Kullanıcı doğru komutu ezberlemek zorunda kalmaz; pencere açılır, giriş
    akışı orada yürür (parola/kod her zaman kullanıcıda kalır).
    """
    root = root or Path.cwd()
    info = auth_command(agent, root)
    if not info["ok"]:
        return info
    if not IS_WIN:
        return {
            "ok": False,
            "detail": "Otomatik terminal yalnız Windows'ta; komutu elle çalıştırın.",
        }

    env_prefix = "".join(f'set "{k}={v}" && ' for k, v in info["env"].items())
    # /k: komut bittikten sonra pencere açık kalsın (kullanıcı çıktıyı görsün).
    subprocess.Popen(
        f'start "ATLAS - {agent} giris" cmd /k {env_prefix}{info["command"]}',
        shell=True,
        cwd=str(root),
    )
    return {
        "ok": True,
        "detail": f"{agent} için giriş penceresi açıldı.",
        "command": info["command"],
    }

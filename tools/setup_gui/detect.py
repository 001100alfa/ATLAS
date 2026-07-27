"""ATLAS kurulum sihirbazı — ortam ve bileşen tespiti (yalnız stdlib).

Bu modül kurulumun "gerçek durumunu" çıkarır: hangi çalışma zamanları var,
hangi AI CLI'lar kurulu, yerel AI arka ucu (Ollama) hazır mı, ACP ajanları
kayıtlı mı. Sihirbaz hiçbir şeyi varsaymaz — her ekran bu tespite bakar.

Ajan yolları/env'i `tools/gen-acp-config.js` ile AYNI kuralları izler (bkz.
AGENTS). Burada Python'da tekrar edilmesinin nedeni: node kurulu olmayan bir
makinede de opencode/kimi/goose tespit edilip kaydedilebilsin (JS üretici node
gerektirir). İkisi arasındaki parite `tests/test_setup_gui.py` ile korunur.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

IS_WIN = os.name == "nt"


def _exe(name: str) -> str:
    """Windows'ta çalıştırılabilir uzantısını ekler."""
    return f"{name}.exe" if IS_WIN else name


def project_root() -> Path:
    """Depo kökü: bu dosya <root>/tools/setup_gui/detect.py konumundadır."""
    return Path(__file__).resolve().parents[2]


# --- ortak env yardımcıları (gen-acp-config.js ile aynı) ---------------------


def _home_env(d: Path) -> dict[str, str]:
    """$HOME köklü yazan CLI'lar için proje-yerel ev dizini."""
    return {
        "HOME": str(d),
        "USERPROFILE": str(d),
        "XDG_CONFIG_HOME": str(d / ".config"),
        "XDG_DATA_HOME": str(d / ".local" / "share"),
        "XDG_STATE_HOME": str(d / ".local" / "state"),
        "XDG_CACHE_HOME": str(d / ".cache"),
    }


def _xdg_env(d: Path) -> dict[str, str]:
    """XDG'yi Windows'ta da onurlandıran CLI'lar (OpenCode) için."""
    return {
        "XDG_CONFIG_HOME": str(d / "config"),
        "XDG_DATA_HOME": str(d / "data"),
        "XDG_STATE_HOME": str(d / "state"),
        "XDG_CACHE_HOME": str(d / "cache"),
    }


# --- ajan tanımları ---------------------------------------------------------


def agent_specs(root: Path | None = None) -> dict[str, dict]:
    """Beş ACP ajanının spawn sözleşmesi.

    Juggler ajanı kabuk kullanmadan `exec.LookPath(command)` + `exec.Command`
    ile başlatır. Bu yüzden Node CLI'ları `node <bin>` olarak çağrılır (`.cmd`
    shim'i PE ikili değildir), derlenmiş/Python ikilileri mutlak yolla.
    """
    root = root or project_root()
    aicli = root / "tools" / "ai-cli"
    home = aicli / "home"

    return {
        "opencode": {
            "label": "OpenCode",
            "kind": "npm (derlenmiş ikili)",
            "bin": aicli / "node_modules" / "opencode-ai" / "bin" / _exe("opencode"),
            "needs_node": False,
            "command_from_bin": True,  # command = bin yolu
            "args": ["acp"],
            "env": _xdg_env(home),
            "keyless": False,
            "auth_hint": "opencode auth login",
        },
        "kilo": {
            "label": "Kilo",
            "kind": "npm (Node)",
            "bin": aicli / "node_modules" / "@kilocode" / "cli" / "bin" / "kilo",
            "needs_node": True,
            "command_from_bin": False,  # command = node, args = [bin, ...]
            "args": ["acp"],
            "env": _home_env(home / "kilo-home"),
            "keyless": False,
            "auth_hint": "kilo auth login",
        },
        "cline": {
            "label": "Cline",
            "kind": "npm (Node)",
            "bin": aicli / "node_modules" / "cline" / "bin" / "cline",
            "needs_node": True,
            "command_from_bin": False,
            "args": ["--acp"],
            "env": _home_env(home / "cline-home"),
            "keyless": False,
            # Cline ACP'si her oturumda bulut kimliği ister; device-code akışı.
            "auth_cmd": ["auth", "cline"],
            "auth_device_flow": True,
            "auth_hint": "cline auth cline (tarayıcıda cihaz kodu)",
        },
        "kimi": {
            "label": "Kimi",
            "kind": "pip (Python)",
            "bin": aicli / "py-venv" / ("Scripts" if IS_WIN else "bin") / _exe("kimi"),
            "needs_node": False,
            "command_from_bin": True,
            "args": ["acp"],
            "env": _home_env(home / "kimi-home"),
            # ÖLÇÜLDÜ: pip `kimi-cli` ACP sunucusu session/new'de _check_auth()'u
            # KOŞULSUZ çağırır (kimi_cli/acp/server.py) — Kimi hesabı token'ı
            # şarttır, yerel model ayarı bu kapıyı açmaz. (Juggler'daki npm
            # `kimi-code` paketi farklı davranır ve anahtarsız çalışabilir.)
            "keyless": False,
            "local_model_ok": True,  # yerel model doğrudan CLI kullanımında geçerli
            "auth_hint": "kimi login (ACP hesap ister)",
        },
        "goose": {
            "label": "Goose",
            "kind": "Windows ikili (Rust)",
            "bin": root / "tools" / "goose" / "goose-package" / _exe("goose"),
            "needs_node": False,
            "command_from_bin": True,
            "args": ["acp"],
            "env": _home_env(root / "tools" / "goose" / "home"),
            "keyless": True,
            "auth_hint": "yerel Ollama (hesapsız) veya GOOSE_PROVIDER",
        },
    }


def acp_entry(name: str, spec: dict) -> dict:
    """Bir ajanın acp.json girdisi (command/args/env)."""
    node = shutil.which("node") or "node"
    if spec["command_from_bin"]:
        command, args = str(spec["bin"]), list(spec["args"])
    else:
        command, args = node, [str(spec["bin"]), *spec["args"]]
    return {"command": command, "args": args, "env": dict(spec["env"])}


# --- Ollama (yerel, anahtarsız arka uç) -------------------------------------

OLLAMA_PORT = 11435  # portable örnek; sistem kurulumunun 11434'üne dokunmaz


def _port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.35) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def detect_ollama(root: Path | None = None) -> dict:
    """Yerel Ollama durumu: proje-içi portable, sistem kurulumu, çalışıyor mu."""
    root = root or project_root()
    portable = root / "tools" / "ollama" / _exe("ollama")
    system = shutil.which("ollama")
    if not system and IS_WIN:
        guess = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
        if guess.is_file():
            system = str(guess)

    models_dir = root / "tools" / "ollama" / "models"
    has_model = False
    if models_dir.is_dir():
        manifests = models_dir / "manifests"
        has_model = manifests.is_dir() and any(manifests.rglob("*"))

    # Not: port_open, o portu KİMİN sunduğunu bilmez (başka bir kurulumun
    # portable örneği de olabilir). Anahtarsız ajanlar için önemli olan budur:
    # portta konuşan bir Ollama varsa çalışırlar.
    return {
        "portable_installed": portable.is_file(),
        "portable_path": str(portable),
        "portable_has_model": has_model,
        "port_serving": _port_open(OLLAMA_PORT),
        "system_path": system,
        "system_running": _port_open(11434),
        "port": OLLAMA_PORT,
        "backend_available": _port_open(OLLAMA_PORT) or _port_open(11434),
    }


# --- çalışma zamanları ------------------------------------------------------


def detect_runtimes(root: Path | None = None) -> dict:
    """Python (gömülü/sistem), Node ve npm durumu."""
    root = root or project_root()
    embedded = root / "runtime" / "python" / "cpython-3.12.13-windows-x86_64-none" / _exe("python")
    venv = root / "runtime" / "venv" / ("Scripts" if IS_WIN else "bin") / _exe("python")
    dotvenv = root / ".venv" / ("Scripts" if IS_WIN else "bin") / _exe("python")

    node = shutil.which("node")
    npm = shutil.which("npm")
    return {
        "python_embedded": str(embedded) if embedded.is_file() else None,
        "python_running": sys.executable,
        "venv": str(venv) if venv.is_file() else (str(dotvenv) if dotvenv.is_file() else None),
        "node": node,
        "node_version": _version(node, "--version"),
        "npm": npm,
        # npm Windows'ta .cmd shim'dir; kabuk üzerinden sürüm sorulur.
        "npm_version": _version(npm, "--version", shell_ok=True),
    }


def _version(exe: str | None, flag: str, shell_ok: bool = False) -> str | None:
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, flag],
            capture_output=True,
            text=True,
            timeout=15,
            shell=shell_ok and IS_WIN,
        )
        return (out.stdout or out.stderr).strip().splitlines()[0] if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


# --- ACP kaydı --------------------------------------------------------------


# --- projeyi çalıştırma -----------------------------------------------------

# Sihirbazın başlatmasına izin verilen betikler. Beyaz liste: arayüzden gelen ad
# doğrudan çalıştırılmaz, yalnız buradaki karşılığı çalıştırılır.
LAUNCHERS = {
    "desktop": {
        "script": "juggler-desktop_Run.bat",
        "label": "Masaüstü paneli",
        "hint": "Ayrı bir pencerede açılır (tarayıcı gerekmez).",
        "needs": ("tools/juggler/juggler.exe", "tools/juggler/juggler-app.exe"),
    },
    "webui": {
        "script": "juggler-webui_Run.bat",
        "label": "Web arayüzü",
        "hint": "Sunucu başlar, adres konsolda yazar; tarayıcıdan açarsınız.",
        "needs": ("tools/juggler/juggler.exe",),
    },
    "cli": {
        # atlas.cmd DEĞİL: o argparse ile alt komut ister, argümansız çağrılınca
        # kullanım hatası basıp pencereyi anında kapatır (kullanıcıya "CLI
        # çalışmıyor" gibi görünür). atlas-shell.cmd açık kalan bir konsol verir.
        "script": "atlas-shell.cmd",
        "label": "Komut satırı (ATLAS CLI)",
        "hint": "Komut yazabileceğiniz bir konsol açar (atlas, atlas-sections).",
        "needs": (),
    },
}


def detect_launchers(root: Path | None = None) -> dict:
    """Hangi çalıştırma yollarının GERÇEKTEN kullanılabilir olduğunu söyler.

    Panel ikilileri depoda tutulmaz (AGPL, büyük — kaynaktan üretilir), bu yüzden
    "çalıştır" düğmesi varsayım yapamaz; her seçeneğin ön koşulu tek tek bakılır.
    """
    root = root or project_root()
    out: dict[str, dict] = {}
    for key, spec in LAUNCHERS.items():
        script = root / spec["script"]
        missing = [n for n in spec["needs"] if not (root / n).is_file()]
        out[key] = {
            "label": spec["label"],
            "hint": spec["hint"],
            "script": spec["script"],
            "available": script.is_file() and not missing,
            "missing": missing if script.is_file() else [spec["script"]],
        }
    # Önerilen: masaüstü > web > CLI (kullanıcıya en az iş çıkaran).
    out["preferred"] = next(
        (k for k in ("desktop", "webui", "cli") if out[k]["available"]), None
    )
    return out


def acp_config_paths(root: Path | None = None) -> dict[str, Path]:
    """Juggler'ın okuduğu iki config: global ve proje (proje global'i ezer)."""
    root = root or project_root()
    return {
        "global": Path.home() / ".juggler" / "acp.json",
        "project": root / ".juggler" / "acp.json",
    }


def classify_source(command: str, root: Path | None = None) -> dict:
    """Kayıtlı bir ajanın komutunun HANGİ kurulumdan geldiğini söyler.

    Aynı makinede birden fazla kurulum olabilir (ör. ATLAS ve ayrı bir Juggler
    deposu, her biri kendi CLI'larıyla). Panel yalnız birini çalıştırır; sihirbaz
    da hangisinin bağlı olduğunu göstermek zorunda — yoksa kullanıcı yanlış
    kurulumu onarmaya çalışır.
    """
    root = (root or project_root()).resolve()
    try:
        p = Path(command).resolve()
    except (OSError, ValueError):
        return {"kind": "other", "label": "bilinmiyor", "root": None}

    wrappers = root.joinpath(*("tools", "agents"))
    if p.is_relative_to(wrappers):
        return {"kind": "atlas-wrapper", "label": "ATLAS (sarmalayıcı)", "root": str(root)}
    if p.is_relative_to(root):
        return {"kind": "atlas-direct", "label": "ATLAS (doğrudan)", "root": str(root)}

    # Depo dışı: kurulumun kökünü bulmaya çalış (.toolchain / .juggler işareti).
    for parent in p.parents:
        if (parent / ".toolchain").is_dir() or (parent / ".juggler").is_dir():
            return {
                "kind": "external",
                "label": f"Diğer kurulum: {parent.name}",
                "root": str(parent),
            }
    if Path(command).name.lower() in {"node", "node.exe", "cmd", "cmd.exe"}:
        return {"kind": "system", "label": "Sistem yorumlayıcısı", "root": None}
    return {"kind": "external", "label": f"Depo dışı: {p.parent.name}", "root": str(p.parent)}


def detect_registration(root: Path | None = None) -> dict:
    """Hangi ajanların acp.json'a kayıtlı olduğunu ve kaynaklarını okur."""
    root = root or project_root()
    result: dict = {"registered": {}, "sources": {}, "files": {}, "installations": {}}
    for scope, path in acp_config_paths(root).items():
        entry: dict = {"path": str(path), "exists": path.is_file(), "agents": []}
        if path.is_file():
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                agents = doc.get("acpAgents") or {}
                entry["agents"] = sorted(agents)
                for name, cfg in agents.items():
                    result["registered"][name] = scope  # proje sonra gelir, ezer
                    cmd = (cfg or {}).get("command") or ""
                    # Node CLI'larda asıl kaynak args[0] (betik), command değil.
                    probe = cmd
                    if Path(cmd).name.lower() in {"node", "node.exe"}:
                        args = (cfg or {}).get("args") or []
                        probe = args[0] if args else cmd
                    src = classify_source(probe, root)
                    result["sources"][name] = src
                    if src["root"]:
                        result["installations"].setdefault(
                            src["root"], {"label": src["label"], "agents": []}
                        )["agents"].append(name)
            except (OSError, json.JSONDecodeError) as exc:
                entry["error"] = str(exc)
        result["files"][scope] = entry
    return result


# --- birleşik durum ---------------------------------------------------------


def detect_all(root: Path | None = None) -> dict:
    """Sihirbazın her ekranda kullandığı tam durum anlık görüntüsü."""
    root = root or project_root()
    runtimes = detect_runtimes(root)
    registration = detect_registration(root)
    specs = agent_specs(root)

    agents = []
    for name, spec in specs.items():
        installed = Path(spec["bin"]).is_file()
        blocked = spec["needs_node"] and not runtimes["node"]
        agents.append(
            {
                "name": name,
                "label": spec["label"],
                "kind": spec["kind"],
                "installed": installed,
                "needs_node": spec["needs_node"],
                "node_missing": blocked,
                "keyless": spec["keyless"],
                "auth_hint": spec["auth_hint"],
                "device_flow": bool(spec.get("auth_device_flow")),
                "registered": registration["registered"].get(name),
                "source": registration["sources"].get(name),
            }
        )

    core_ready = bool(runtimes["venv"])
    clis_installed = [a for a in agents if a["installed"]]

    return {
        "root": str(root),
        "runtimes": runtimes,
        "ollama": detect_ollama(root),
        "agents": agents,
        "registration": registration,
        "launchers": detect_launchers(root),
        "summary": {
            "core_ready": core_ready,
            "clis_installed": len(clis_installed),
            "clis_total": len(agents),
            "agents_registered": len(registration["registered"]),
        },
    }


if __name__ == "__main__":  # elle inceleme: python -m tools.setup_gui.detect
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(detect_all(), indent=2, ensure_ascii=False))

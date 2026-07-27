"""Ajan sarmalayıcıları (`tools/agents/*.cmd`) üretir.

Juggler kurulumunda kanıtlanmış yaklaşımın ATLAS'a taşınmış hâli. Ajanı doğrudan
`acp.json`'dan çağırmak yerine ince bir `.cmd` üzerinden çağırırız. Kazandırdığı:

* **Tek yerde ortam.** Ajanın config/state'ini proje içinde tutan değişkenler
  sarmalayıcıda durur; değiştirmek için `acp.json`'u yeniden yazmak gerekmez.
* **Kapatılan sızıntı.** goose Windows'ta XDG'yi yok sayar, kökünü `%APPDATA%`
  üzerinden çözer (Rust `dirs`). ÖLÇÜLDÜ: yalnız HOME/XDG verilince ayarlarını
  kullanıcının gerçek `%APPDATA%\\Block\\goose` dizinine yazıyordu. Sarmalayıcı
  `APPDATA`'yı da proje içine çevirir.
* **Kendiliğinden başlayan yerel model.** Anahtarsız ajanlar (goose)
  `ensure-ollama.cmd` çağırır; sunucu kapalıysa (ör. makine yeniden başladıysa)
  ajan çalışmadan önce ayağa kaldırılır. Doğrudan kayıtta bunu yapacak yer yoktu.

Juggler ajanı `exec.LookPath` + `exec.Command` ile kabuksuz başlatır; `.cmd`
Windows'ta bu yolla çalışır (Go ve Python subprocess ile ölçüldü).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .detect import IS_WIN, OLLAMA_PORT, _exe, agent_specs

WRAPPER_DIR = ("tools", "agents")
# Uretilen dosyalar SAF ASCII olmali: cmd.exe konsol kod sayfasina gore (cp857/
# cp1254) Turkce karakterleri bozar ve komutu kirabilir.
HEADER = (
    "@echo off\n"
    "rem ATLAS kurulum sihirbazi tarafindan uretildi - elle duzenlemeyin.\n"
    "rem Yeniden uretmek: sihirbazda 5. adim > 'ATLAS sarmalayicilarina gec'.\n"
    "setlocal\n"
    'set "ROOT=%~dp0..\\.."\n'
)


def wrapper_dir(root: Path) -> Path:
    return root.joinpath(*WRAPPER_DIR)


def wrapper_path(root: Path, agent: str) -> Path:
    return wrapper_dir(root) / f"{agent}.cmd"


def _rel(root: Path, p: Path) -> str:
    """Yolu %ROOT% köklü göreli biçime çevirir (klasör taşınabilir kalsın)."""
    try:
        return "%ROOT%\\" + str(p.relative_to(root)).replace("/", "\\")
    except ValueError:
        return str(p)  # depo dışında (olmamalı) — mutlak bırak


def _ensure_ollama_cmd(root: Path) -> str:
    """Yerel model sunucusunu gerekiyorsa başlatan yardımcı (idempotent)."""
    exe = _rel(root, root / "tools" / "ollama" / _exe("ollama"))
    models = _rel(root, root / "tools" / "ollama" / "models")
    return (
        "@echo off\n"
        f"rem ATLAS - yerel model sunucusunu (127.0.0.1:{OLLAMA_PORT}) gerekiyorsa baslatir.\n"
        "rem Kurulu degilse sessizce cikar: ajan kendi hesabiyla calismaya devam eder.\n"
        "setlocal\n"
        'set "ROOT=%~dp0..\\.."\n'
        f'set "OLLAMA_EXE={exe}"\n'
        f'if not exist "%OLLAMA_EXE%" exit /b 0\n'
        f'set "OLLAMA_MODELS={models}"\n'
        f'set "OLLAMA_HOST=127.0.0.1:{OLLAMA_PORT}"\n'
        "\n"
        "rem Ayakta mi? `list` basariyla donerse evet.\n"
        '"%OLLAMA_EXE%" list >nul 2>&1\n'
        "if not errorlevel 1 exit /b 0\n"
        "\n"
        "rem Degilse ayri pencerede baslat ve hazir olmasini bekle (~20 sn).\n"
        'start "ATLAS yerel model" /min "%OLLAMA_EXE%" serve\n'
        "for /L %%i in (1,1,40) do (\n"
        '  "%OLLAMA_EXE%" list >nul 2>&1\n'
        "  if not errorlevel 1 exit /b 0\n"
        "  >nul ping -n 2 127.0.0.1\n"
        ")\n"
        "echo [ensure-ollama] UYARI: yerel model sunucusu acilmadi. 1>&2\n"
        "exit /b 0\n"
    )


def _agent_cmd(root: Path, name: str, spec: dict) -> str:
    """Tek bir ajanın sarmalayıcısı."""
    bin_path = _rel(root, Path(spec["bin"]))
    lines = [HEADER, f'set "BIN={bin_path}"\n']
    lines.append(
        f'if not exist "%BIN%" ( echo [{name}] kurulu degil: %BIN% 1>&2 & exit /b 1 )\n\n'
    )

    lines.append("rem --- config/state proje icinde kalsin ---\n")
    for key, value in sorted(spec["env"].items()):
        lines.append(f'set "{key}={_rel(root, Path(value))}"\n')

    if name == "goose":
        # goose Windows'ta XDG'yi yok sayar; kokunu %APPDATA%'dan cozer (olculdu).
        home = _rel(root, Path(spec["env"]["HOME"]))
        lines.append(
            "rem goose Windows'ta XDG'yi yok sayar, kokunu %APPDATA%'dan cozer (Rust dirs).\n"
            f'set "APPDATA={home}"\n'
        )
    if name == "cline":
        home = _rel(root, Path(spec["env"]["HOME"]))
        lines.append(f'set "CLINE_DIR={home}"\n')

    if spec.get("keyless"):
        # Model secimi sihirbazin yazdigi local-model.cmd'de durur; sarmalayici
        # sabit kalir. (local-model.cmd setlocal KULLANMAZ, degiskenler buraya
        # sizsin diye.) Yoksa makul varsayilanlara duseriz.
        lines.append(
            "\nrem --- anahtarsiz yerel model ---\n"
            'call "%~dp0ensure-ollama.cmd"\n'
            'if exist "%~dp0local-model.cmd" call "%~dp0local-model.cmd"\n'
            'if not defined GOOSE_PROVIDER set "GOOSE_PROVIDER=ollama"\n'
            f'if not defined OLLAMA_HOST set "OLLAMA_HOST=http://127.0.0.1:{OLLAMA_PORT}"\n'
        )

    lines.append("\n")
    if spec["command_from_bin"]:
        lines.append('"%BIN%" %*\n')
    else:
        # Node CLI: `.cmd` shim'i PE degil, bare ad PATH'te olmayabilir.
        node = shutil.which("node") or "node"
        lines.append(f'set "NODE={node}"\n"%NODE%" "%BIN%" %*\n')
    lines.append("exit /b %ERRORLEVEL%\n")
    return "".join(lines)


def generate(root: Path, agents: list[str] | None = None) -> dict:
    """Sarmalayıcıları yazar; yalnız kurulu ajanlar için."""
    if not IS_WIN:
        return {"ok": False, "detail": "Sarmalayıcılar şimdilik yalnız Windows için."}

    specs = agent_specs(root)
    names = agents or list(specs)
    d = wrapper_dir(root)
    d.mkdir(parents=True, exist_ok=True)

    (d / "ensure-ollama.cmd").write_text(_ensure_ollama_cmd(root), encoding="ascii", newline="\r\n")

    written, skipped = [], []
    for name in names:
        spec = specs.get(name)
        if not spec or not Path(spec["bin"]).is_file():
            skipped.append(name)
            continue
        # .cmd dosyalari CRLF ve ASCII olmali (cmd.exe Turkce karakterle bogulur).
        wrapper_path(root, name).write_text(
            _agent_cmd(root, name, spec), encoding="ascii", newline="\r\n"
        )
        written.append(name)

    return {"ok": True, "dir": str(d), "written": written, "skipped": skipped}


def write_local_model(root: Path, base_url: str, model: str, provider: str = "ollama") -> Path:
    """Kullanıcının seçtiği yerel modeli sarmalayıcıların okuduğu dosyaya yazar.

    `setlocal` YOK: değişkenler `call` eden sarmalayıcıya sızmalı.
    """
    d = wrapper_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "local-model.cmd"
    path.write_text(
        "@echo off\n"
        "rem ATLAS kurulum sihirbazi tarafindan uretildi - yerel model secimi.\n"
        "rem setlocal YOK: bu degiskenler cagiran sarmalayiciya gecmeli.\n"
        f'set "GOOSE_PROVIDER={provider}"\n'
        f'set "GOOSE_MODEL={model}"\n'
        f'set "OLLAMA_HOST={base_url}"\n',
        encoding="ascii",
        newline="\r\n",
    )
    return path


def wrapper_entry(root: Path, agent: str, spec: dict) -> dict:
    """Sarmalayıcıyı kullanan acp.json girdisi (env sarmalayıcıda, burada değil)."""
    return {"command": str(wrapper_path(root, agent)), "args": list(spec["args"]), "env": {}}

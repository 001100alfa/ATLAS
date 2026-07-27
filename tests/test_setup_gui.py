"""Kurulum sihirbazı: tespit, ajan sözleşmeleri ve JS üreticiyle parite.

Ağ/kurulum gerektirmez: ajan ikilileri sahte dosyalarla taklit edilir.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from setup_gui import connect, wrappers  # noqa: E402
from setup_gui.acp_probe import _classify, effective_entry  # noqa: E402
from setup_gui.detect import (  # noqa: E402
    IS_WIN,
    acp_entry,
    agent_specs,
    classify_source,
    detect_all,
    detect_launchers,
    detect_registration,
)

AGENTS = ("opencode", "kilo", "cline", "kimi", "goose")


def _stub_tree(root: Path) -> None:
    """Beş ajanın ikilisini sahte dosyalarla oluşturur (gen-acp-config.js ile aynı yollar)."""
    exe = ".exe" if IS_WIN else ""
    files = [
        f"tools/ai-cli/node_modules/opencode-ai/bin/opencode{exe}",
        "tools/ai-cli/node_modules/@kilocode/cli/bin/kilo",
        "tools/ai-cli/node_modules/cline/bin/cline",
        f"tools/ai-cli/py-venv/{'Scripts' if IS_WIN else 'bin'}/kimi{exe}",
        f"tools/goose/goose-package/goose{exe}",
    ]
    for rel in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("stub", encoding="utf-8")


def test_agent_specs_cover_all_agents() -> None:
    assert set(agent_specs(Path("/x"))) == set(AGENTS)


def test_node_clis_invoke_node_not_shim() -> None:
    """Kilo/Cline `node <bin>` ile çağrılmalı: `.cmd` shim'i PE değildir, Juggler exec eder."""
    specs = agent_specs(Path("/x"))
    for name in ("kilo", "cline"):
        entry = acp_entry(name, specs[name])
        assert Path(entry["command"]).stem == "node"
        assert entry["args"][0].endswith(("kilo", "cline"))
    for name in ("opencode", "kimi", "goose"):
        entry = acp_entry(name, specs[name])
        assert Path(entry["command"]).stem not in {"node", "cmd"}


def test_cline_uses_acp_flag_others_use_subcommand() -> None:
    specs = agent_specs(Path("/x"))
    assert specs["cline"]["args"] == ["--acp"]
    for name in ("opencode", "kimi", "goose", "kilo"):
        assert specs[name]["args"] == ["acp"]


def test_env_is_project_local(tmp_path: Path) -> None:
    """Hiçbir ajan kullanıcının gerçek ev dizinine yazmamalı."""
    for name, spec in agent_specs(tmp_path).items():
        for key, value in spec["env"].items():
            assert str(tmp_path) in value, f"{name}.{key} proje dışına işaret ediyor: {value}"


def test_register_agents_writes_only_installed(tmp_path: Path) -> None:
    _stub_tree(tmp_path)
    res = connect.register_agents(tmp_path)
    doc = json.loads((tmp_path / ".juggler" / "acp.json").read_text(encoding="utf-8"))
    assert set(doc["acpAgents"]) == set(AGENTS)
    assert res["skipped"] == []


def test_register_agents_skips_missing(tmp_path: Path) -> None:
    res = connect.register_agents(tmp_path)  # hiçbir ikili yok
    assert res["written"] == []
    assert set(res["skipped"]) == set(AGENTS)


def test_register_preserves_keyless_env_without_wrappers(tmp_path: Path) -> None:
    """Sarmalayıcısız (eski) kayıtta env kayda gömülür ve korunmalı."""
    _stub_tree(tmp_path)
    connect.register_agents(tmp_path, use_wrappers=False)
    path = tmp_path / ".juggler" / "acp.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["acpAgents"]["goose"]["env"]["GOOSE_PROVIDER"] = "ollama"
    path.write_text(json.dumps(doc), encoding="utf-8")

    connect.register_agents(tmp_path, use_wrappers=False)
    doc2 = json.loads(path.read_text(encoding="utf-8"))
    assert doc2["acpAgents"]["goose"]["env"]["GOOSE_PROVIDER"] == "ollama"


# --- sarmalayıcılar ---------------------------------------------------------


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_register_uses_wrappers_by_default(tmp_path: Path) -> None:
    _stub_tree(tmp_path)
    res = connect.register_agents(tmp_path)
    assert set(res["wrapped"]) == set(AGENTS)
    doc = json.loads((tmp_path / ".juggler" / "acp.json").read_text(encoding="utf-8"))
    for name in AGENTS:
        entry = doc["acpAgents"][name]
        assert entry["command"].endswith(f"tools\\agents\\{name}.cmd")
        # Ortam artık sarmalayıcıda; kayıt sade kalır.
        assert entry["env"] == {}


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_wrappers_are_ascii_and_crlf(tmp_path: Path) -> None:
    """cmd.exe konsol kod sayfasinda Turkce karakterleri bozar; saf ASCII sart."""
    _stub_tree(tmp_path)
    wrappers.generate(tmp_path)
    for p in (tmp_path / "tools" / "agents").glob("*.cmd"):
        raw = p.read_bytes()
        raw.decode("ascii")  # ASCII değilse UnicodeDecodeError
        assert b"\r\n" in raw, p.name


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_goose_wrapper_redirects_appdata(tmp_path: Path) -> None:
    """ÖLÇÜLDÜ: goose Windows'ta kökünü %APPDATA%'dan çözer; proje içine çevrilmeli."""
    _stub_tree(tmp_path)
    wrappers.generate(tmp_path)
    text = (tmp_path / "tools" / "agents" / "goose.cmd").read_text(encoding="ascii")
    assert 'set "APPDATA=%ROOT%\\tools\\goose\\home"' in text
    assert 'call "%~dp0ensure-ollama.cmd"' in text


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_local_model_file_has_no_setlocal(tmp_path: Path) -> None:
    """Değişkenler çağıran sarmalayıcıya sızmalı; setlocal bunu engeller."""
    wrappers.write_local_model(tmp_path, "http://127.0.0.1:11435", "llama3.2:3b")
    text = (tmp_path / "tools" / "agents" / "local-model.cmd").read_text(encoding="ascii")
    # KOMUT olarak setlocal olmamalı; 'rem' yorumunda geçmesi sorun değil.
    commands = [
        ln.strip().lower()
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().lower().startswith("rem")
    ]
    assert not any(c == "setlocal" or c.startswith("setlocal ") for c in commands)
    assert 'set "GOOSE_MODEL=llama3.2:3b"' in text


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_keyless_goose_writes_local_model_when_wrapped(tmp_path: Path) -> None:
    _stub_tree(tmp_path)
    connect.register_agents(tmp_path)  # sarmalayıcıları üretir
    res = connect._keyless_goose(tmp_path, "http://127.0.0.1:11435", "llama3.1:8b")
    assert res["ok"]
    text = (tmp_path / "tools" / "agents" / "local-model.cmd").read_text(encoding="ascii")
    assert "llama3.1:8b" in text


# --- kaynak sınıflandırma (iki kurulum tek görünüm) -------------------------


def test_classify_source_distinguishes_installations(tmp_path: Path) -> None:
    atlas = tmp_path / "ATLAS"
    (atlas / "tools" / "agents").mkdir(parents=True)
    other = tmp_path / "juggler"
    (other / ".toolchain").mkdir(parents=True)

    assert classify_source(str(atlas / "tools" / "agents" / "goose.cmd"), atlas)["kind"] == (
        "atlas-wrapper"
    )
    assert classify_source(str(atlas / "tools" / "goose" / "goose.exe"), atlas)["kind"] == (
        "atlas-direct"
    )
    ext = classify_source(str(other / "scripts" / "goose.cmd"), atlas)
    assert ext["kind"] == "external" and "juggler" in ext["label"]


def test_registration_reports_sources(tmp_path: Path) -> None:
    """Kayıt okuması hangi ajanın nereden geldiğini söylemeli."""
    _stub_tree(tmp_path)
    connect.register_agents(tmp_path)
    reg = detect_registration(tmp_path)
    assert reg["sources"]["goose"]["kind"] in {"atlas-wrapper", "atlas-direct"}
    assert str(tmp_path.resolve()) in reg["installations"]


def test_effective_entry_prefers_registered_config(tmp_path: Path) -> None:
    """Test, spec'i değil Juggler'ın okuyacağı kaydı kullanmalı."""
    _stub_tree(tmp_path)
    connect.register_agents(tmp_path)
    path = tmp_path / ".juggler" / "acp.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["acpAgents"]["goose"]["env"]["GOOSE_PROVIDER"] = "ollama"
    path.write_text(json.dumps(doc), encoding="utf-8")

    entry = effective_entry("goose", agent_specs(tmp_path)["goose"], tmp_path)
    assert entry["env"]["GOOSE_PROVIDER"] == "ollama"


def test_keyless_kimi_writes_kimi_cli_schema(tmp_path: Path) -> None:
    """pip `kimi-cli`: config `$HOME/.kimi/config.toml`, tip `openai_legacy`."""
    res = connect._keyless_kimi(tmp_path, "http://127.0.0.1:11435", "llama3.1:8b")
    cfg = tmp_path / "tools" / "ai-cli" / "home" / "kimi-home" / ".kimi" / "config.toml"
    assert res["ok"] and cfg.is_file()
    text = cfg.read_text(encoding="utf-8")
    assert 'type = "openai_legacy"' in text
    assert 'base_url = "http://127.0.0.1:11435/v1"' in text


def test_pick_model_prefers_tool_capable() -> None:
    assert connect.pick_model(["gemma:2b", "qwen2.5-coder:7b"]) == "qwen2.5-coder:7b"
    assert connect.pick_model(["mystery:1b"]) == "mystery:1b"
    assert connect.pick_model([]) is None


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Authentication required: Call authenticate", "needs_auth"),
        ("Failed to resolve provider: GOOSE_PROVIDER", "needs_provider"),
        ("something exploded", "error"),
    ],
)
def test_classify_maps_agent_errors(message: str, expected: str) -> None:
    assert _classify(message) == expected


@pytest.mark.parametrize(
    "model",
    ["llama3.2:3b", "qwen2.5-coder:7b", "llama3.2", "some/ns-model:tag"],
)
def test_model_names_accepted(model: str) -> None:
    from setup_gui.install_ollama import MODEL_RE

    assert MODEL_RE.match(model)


@pytest.mark.parametrize(
    "model",
    ["../evil", "a b", "x;rm -rf /", "$(whoami)", "-flag", "a" * 200],
)
def test_model_names_rejected(model: str) -> None:
    """Model adı doğrudan argv'ye gider; kabuk yok ama yine de dar tutulur."""
    from setup_gui.install_ollama import MODEL_RE

    assert not MODEL_RE.match(model)


def test_install_ollama_job_rejects_bad_model() -> None:
    from setup_gui import server

    assert server._cmd("install-ollama", {"model": "llama3.2:3b"})
    assert server._cmd("install-ollama", {"model": "x;calc.exe"}) is None
    # Boş değer varsayılana düşer (güvenli), bilinmeyen görev reddedilir.
    assert server._cmd("install-ollama", {"model": ""})
    assert server._cmd("bilinmeyen-gorev") is None


# --- indirme dayanıklılığı --------------------------------------------------


class _FakeResp:
    """urlopen yanıtı taklidi: gövdeyi parça parça verir, erken kesilebilir."""

    def __init__(self, body: bytes, status: int = 200, headers: dict | None = None):
        self._body = body
        self._pos = 0
        self.status = status
        self.headers = headers or {"Content-Length": str(len(body))}

    def read(self, n: int = -1) -> bytes:
        chunk = self._body[self._pos : self._pos + (n if n > 0 else len(self._body))]
        self._pos += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_truncated_download_is_not_promoted(tmp_path: Path, monkeypatch) -> None:
    """ÖLÇÜLDÜ: akış erken kapanabiliyor; yarım dosya asla teslim edilmemeli."""
    from setup_gui import install_ollama as io

    calls: list[str | None] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.get_header("Range"))
        # Her denemede toplam 100 bayttan yalnız 40 bayt gönder (hep eksik).
        return _FakeResp(b"x" * 40, 200, {"Content-Length": "100"})

    monkeypatch.setattr(io.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(io.time, "sleep", lambda *_: None)

    dest = tmp_path / "a.zip"
    with pytest.raises(RuntimeError):
        io.download("http://x/a.zip", dest, attempts=2)
    assert not dest.exists(), "yarım dosya teslim edilmemeli"
    assert (tmp_path / "a.zip.part").exists(), ".part devam icin korunmali"


def test_download_resumes_with_range_header(tmp_path: Path, monkeypatch) -> None:
    """İkinci denemede kalınan yerden devam edilmeli (Range gönderilir)."""
    from setup_gui import install_ollama as io

    seen: list[str | None] = []

    def fake_urlopen(req, timeout=0):
        rng = req.get_header("Range")
        seen.append(rng)
        if rng is None:  # ilk tur: eksik gönder
            return _FakeResp(b"x" * 40, 200, {"Content-Length": "100"})
        # ikinci tur: kalan 60 baytı kısmi yanıt olarak ver
        return _FakeResp(b"y" * 60, 206, {"Content-Range": "bytes 40-99/100"})

    monkeypatch.setattr(io.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(io.time, "sleep", lambda *_: None)

    dest = tmp_path / "b.zip"
    io.download("http://x/b.zip", dest, attempts=3)
    assert dest.is_file() and dest.stat().st_size == 100
    assert seen[0] is None and seen[1] == "bytes=40-"
    assert not (tmp_path / "b.zip.part").exists()


def test_download_restarts_when_server_ignores_range(tmp_path: Path, monkeypatch) -> None:
    """Sunucu Range'i yok sayıp 200 dönerse baştan yazılmalı (dosya bozulmasın)."""
    from setup_gui import install_ollama as io

    state = {"n": 0}

    def fake_urlopen(req, timeout=0):
        state["n"] += 1
        if state["n"] == 1:
            return _FakeResp(b"x" * 40, 200, {"Content-Length": "100"})
        return _FakeResp(b"z" * 100, 200, {"Content-Length": "100"})  # Range yok sayıldı

    monkeypatch.setattr(io.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(io.time, "sleep", lambda *_: None)

    dest = tmp_path / "c.zip"
    io.download("http://x/c.zip", dest, attempts=3)
    assert dest.read_bytes() == b"z" * 100, "eski parça uzerine eklenmemeli"


# --- projeyi çalıştırma -----------------------------------------------------


def test_launchers_report_missing_prerequisites(tmp_path: Path) -> None:
    """Panel ikilileri depoda tutulmaz; düğme varsayım yapmamalı."""
    found = detect_launchers(tmp_path)  # boş dizin: hiçbir betik yok
    assert found["preferred"] is None
    assert not found["desktop"]["available"]
    assert "juggler-desktop_Run.bat" in found["desktop"]["missing"]


def test_launchers_desktop_needs_both_binaries(tmp_path: Path) -> None:
    (tmp_path / "juggler-desktop_Run.bat").write_text("@echo off", encoding="ascii")
    (tmp_path / "tools" / "juggler").mkdir(parents=True)
    (tmp_path / "tools" / "juggler" / "juggler.exe").write_text("x", encoding="ascii")

    found = detect_launchers(tmp_path)
    # juggler-app.exe yok → masaüstü penceresi acilamaz.
    assert not found["desktop"]["available"]
    assert "tools/juggler/juggler-app.exe" in found["desktop"]["missing"]

    (tmp_path / "tools" / "juggler" / "juggler-app.exe").write_text("x", encoding="ascii")
    assert detect_launchers(tmp_path)["desktop"]["available"]


def test_cli_launcher_opens_interactive_shell_not_bare_cli() -> None:
    """`atlas.cmd` argümansız çağrılırsa argparse hata basar ve pencere kapanır.

    Kullanıcıya "CLI çalışmıyor" gibi görünen bu tuzağa geri düşmemek için CLI
    hedefi açık kalan bir konsol (atlas-shell.cmd) açmalı.
    """
    from setup_gui.detect import LAUNCHERS

    assert LAUNCHERS["cli"]["script"] == "atlas-shell.cmd"
    assert LAUNCHERS["cli"]["script"] != "atlas.cmd"


@pytest.mark.skipif(not IS_WIN, reason="Windows kabuk betiği")
def test_atlas_shell_script_is_interactive_and_sets_path() -> None:
    """Depodaki gerçek betik: PATH'i kurmalı ve `cmd /k` ile açık kalmalı."""
    repo = Path(__file__).resolve().parents[1]
    text = (repo / "atlas-shell.cmd").read_text(encoding="ascii")
    assert "cmd /k" in text, "konsol acik kalmali"
    assert 'set "PATH=%ATLAS_HOME%;%PATH%"' in text, "atlas/atlas-sections PATH'te olmali"
    assert "chcp 65001" in text, "mm^2 / mm^4 ciktisi icin UTF-8 kod sayfasi"


def test_launcher_whitelist_blocks_arbitrary_targets() -> None:
    """Arayüzden gelen ad yalnız bilinen betiklere eşlenmeli."""
    from setup_gui.detect import LAUNCHERS

    assert set(LAUNCHERS) == {"desktop", "webui", "cli"}
    for spec in LAUNCHERS.values():
        script = spec["script"]
        assert "/" not in script and "\\" not in script and ".." not in script


def test_detect_all_shape(tmp_path: Path) -> None:
    snap = detect_all(tmp_path)
    assert {"root", "runtimes", "ollama", "agents", "registration", "summary"} <= set(snap)
    assert len(snap["agents"]) == len(AGENTS)
    assert snap["summary"]["clis_total"] == len(AGENTS)


@pytest.mark.skipif(shutil.which("node") is None, reason="node yok")
def test_parity_with_js_generator(tmp_path: Path) -> None:
    """Python kaydı ile gen-acp-config.js aynı command/args'ı üretmeli.

    İki üretici var (JS: mevcut CLI akışı, Python: node'suz da çalışan sihirbaz);
    ayrışırlarsa panelde ajan bozulur, bu yüzden parite testle sabitlenir.
    """
    repo = Path(__file__).resolve().parents[1]
    _stub_tree(tmp_path)
    subprocess.run(
        ["node", str(repo / "tools" / "gen-acp-config.js"), str(tmp_path)],
        check=True,
        capture_output=True,
    )
    js = json.loads((tmp_path / ".juggler" / "acp.json").read_text(encoding="utf-8"))["acpAgents"]

    (tmp_path / ".juggler" / "acp.json").unlink()
    # Parite doğrudan-kayıt biçimi içindir; sarmalayıcı modu bilinçli olarak farklı
    # (komut .cmd'ye işaret eder, ortam sarmalayıcıda durur).
    connect.register_agents(tmp_path, use_wrappers=False)
    py = json.loads((tmp_path / ".juggler" / "acp.json").read_text(encoding="utf-8"))["acpAgents"]

    assert set(js) == set(py)
    for name in js:
        # Kasıtlı fark: JS `node` (bare, PATH'ten çözülür), Python mutlak `node.exe`.
        # İkisini de Juggler'ın exec.LookPath'i kabul eder; mutlak yol PATH'in dar
        # olduğu ortamlarda da bulunur. Bu yüzden dosya ADI (stem) karşılaştırılır.
        js_cmd = Path(js[name]["command"]).stem.lower()
        py_cmd = Path(py[name]["command"]).stem.lower()
        assert js_cmd == py_cmd, name
        assert js[name]["args"] == py[name]["args"], name
        assert js[name]["env"] == py[name]["env"], name


def test_auth_commands_match_real_subcommands(tmp_path: Path):
    """Her ajanın giriş komutu, CLI'sının GERÇEKTEN desteklediği alt komut olmalı.

    Ölçüldü (2026-07-27, `--help` çıktılarıyla):

    * `kimi` — `auth` diye bir alt komut YOK; giriş `kimi login`.
    * `opencode` / `kilo` — `auth` bir komut GRUBU (list/login/logout); tek başına
      yalnız yardım basar, giriş `auth login` altındadır.
    * `cline` — `auth <yöntem>`; ACP için `auth cline`.

    Varsayılan `["auth"]`e düşmek üçünde de sessizce yanlış komut üretiyordu:
    "Giriş yap" düğmesi hata verip hiçbir şey yapmıyordu.
    """
    expected = {
        "opencode": ["auth", "login"],
        "kilo": ["auth", "login"],
        "cline": ["auth", "cline"],
        "kimi": ["login"],
    }
    specs = agent_specs(tmp_path)
    for name, want in expected.items():
        assert specs[name].get("auth_cmd") == want, f"{name} giriş komutu"

    # goose hesapsızdır: giriş komutu tanımlanmaz (sağlayıcı env ile ayarlanır).
    assert "auth_cmd" not in specs["goose"]

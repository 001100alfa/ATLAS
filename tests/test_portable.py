"""Taşınabilirlik: klasör başka bir makinede açıldığında kendini onarır mı?

Ağ/kurulum gerektirmez — ikililer sahte dosyalarla taklit edilir.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.portable import (  # noqa: E402
    autoupdate,
    ollama_identity,
    package,
    relocate,
    runtimes,
    vendor,
)  # noqa: E402
from tools.setup_gui import wrappers  # noqa: E402
from tools.setup_gui.detect import IS_WIN  # noqa: E402


def _stub_tree(root: Path) -> None:
    """Beş ajanın ikilisi + depo içi node/git (gerçek yollarla aynı yerler)."""
    exe = ".exe" if IS_WIN else ""
    for rel in (
        f"tools/ai-cli/node_modules/opencode-ai/bin/opencode{exe}",
        "tools/ai-cli/node_modules/@kilocode/cli/bin/kilo",
        "tools/ai-cli/node_modules/cline/bin/cline",
        f"tools/ai-cli/py-venv/{'Scripts' if IS_WIN else 'bin'}/kimi{exe}",
        f"tools/goose/goose-package/goose{exe}",
        "tools/node/node.exe",
        "tools/node/npm.cmd",
        "tools/git/usr/bin/bash.exe",
    ):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("stub", encoding="utf-8")


# --- çalışma zamanları: depo içi kopya kazanmalı ------------------------------


def test_bundled_runtimes_win_over_machine(tmp_path: Path):
    _stub_tree(tmp_path)
    assert runtimes.node_exe(tmp_path) == str(tmp_path / "tools" / "node" / "node.exe")
    assert runtimes.git_bash(tmp_path) == tmp_path / "tools" / "git" / "usr" / "bin" / "bash.exe"
    assert runtimes.npm_cmd(tmp_path) == str(tmp_path / "tools" / "node" / "npm.cmd")


def test_runtimes_fall_back_to_machine_when_not_bundled(tmp_path: Path):
    """Depo içi kopya yoksa makinedeki kurulum kullanılır (geliştirme makinesi)."""
    assert runtimes.bundled_node(tmp_path) is None
    assert runtimes.node_exe(tmp_path)  # "node" bile olsa bir dize döner


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_wrappers_use_relative_paths_for_bundled_runtimes(tmp_path: Path):
    """ASIL TAŞINABİLİRLİK TESTİ: sarmalayıcıda mutlak makine yolu KALMAMALI.

    Önceki hâlde node yolu `C:\\Users\\<kisi>\\AppData\\Local\\hermes\\node.exe`
    olarak gömülüyordu; klasör başka bir bilgisayara taşınınca kilo/cline ölürdü.
    """
    _stub_tree(tmp_path)
    wrappers.generate(tmp_path)

    kilo = (tmp_path / "tools" / "agents" / "kilo.cmd").read_text(encoding="ascii")
    assert 'set "NODE=%ROOT%\\tools\\node\\node.exe"' in kilo
    kimi = (tmp_path / "tools" / "agents" / "kimi.cmd").read_text(encoding="ascii")
    assert 'set "KIMI_CLI_GIT_BASH_PATH=%ROOT%\\tools\\git\\usr\\bin\\bash.exe"' in kimi
    # Hiçbir sarmalayıcı test kökünün mutlak yolunu taşımamalı.
    for p in (tmp_path / "tools" / "agents").glob("*.cmd"):
        assert str(tmp_path) not in p.read_text(encoding="ascii"), p.name


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_ollama_probe_is_not_the_hanging_list_command(tmp_path: Path):
    """ÖLÇÜLDÜ: `ollama list` bulut ucuna takılınca süresiz asılıyordu."""
    _stub_tree(tmp_path)
    wrappers.generate(tmp_path)
    text = (tmp_path / "tools" / "agents" / "ensure-ollama.cmd").read_text(encoding="ascii")
    assert "curl.exe" in text and "/api/tags" in text
    assert "-m 3" in text, "zaman asimi olmadan probe yine asilabilir"


# --- yeniden yerleştirme ------------------------------------------------------


def test_fingerprint_changes_with_root(tmp_path: Path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        _stub_tree(d)
    assert relocate.fingerprint(a)["root"] != relocate.fingerprint(b)["root"]


def test_needs_relocate_on_first_run_then_settles(tmp_path: Path, monkeypatch):
    _stub_tree(tmp_path)
    needed, why = relocate.needs_relocate(tmp_path)
    assert needed and why == ["ilk çalıştırma"]

    relocate.write_state(tmp_path, relocate.fingerprint(tmp_path))
    needed, why = relocate.needs_relocate(tmp_path)
    assert not needed and why == []


def test_needs_relocate_detects_moved_folder(tmp_path: Path):
    """Kayıt başka bir yoldan geliyorsa uyarlama şart."""
    _stub_tree(tmp_path)
    stale = relocate.fingerprint(tmp_path)
    stale["root"] = r"D:\eski\makine\ATLAS"
    relocate.write_state(tmp_path, stale)
    needed, why = relocate.needs_relocate(tmp_path)
    assert needed and "root" in why


def test_preflight_reports_missing_without_failing(tmp_path: Path):
    _stub_tree(tmp_path)  # juggler/ollama ikilileri YOK
    ids = {c["id"]: c for c in relocate.preflight(tmp_path)}
    assert ids["runtime.node"]["ok"] and ids["runtime.node"]["portable"]
    assert not ids["bin.juggler"]["ok"] and ids["bin.juggler"]["detail"] == "yok"


# --- otomatik güncelleme ------------------------------------------------------


def test_config_defaults_and_override(tmp_path: Path):
    assert autoupdate.load_config(tmp_path) == autoupdate.DEFAULTS
    (tmp_path / autoupdate.CONFIG_NAME).write_text(
        json.dumps({"autoUpdate": "notify", "bilinmeyen": 1}), encoding="utf-8"
    )
    cfg = autoupdate.load_config(tmp_path)
    assert cfg["autoUpdate"] == "notify" and "bilinmeyen" not in cfg


def test_broken_config_does_not_block_startup(tmp_path: Path):
    (tmp_path / autoupdate.CONFIG_NAME).write_text("{bozuk json", encoding="utf-8")
    assert autoupdate.load_config(tmp_path) == autoupdate.DEFAULTS


def test_due_respects_interval(tmp_path: Path):
    autoupdate.write_state(tmp_path, {"lastCheck": 1000.0})
    assert not autoupdate.due(tmp_path, now=1000.0 + 3600)  # 1 saat sonra: erken
    assert autoupdate.due(tmp_path, now=1000.0 + 25 * 3600)  # 25 saat sonra: zamanı


def test_off_means_no_network_at_all(tmp_path: Path, monkeypatch):
    (tmp_path / autoupdate.CONFIG_NAME).write_text('{"autoUpdate":"off"}', encoding="utf-8")

    def boom(*_a, **_k):  # ağa çıkılırsa test patlar
        raise AssertionError("kapaliyken uzak sorgu yapilmamali")

    monkeypatch.setattr(autoupdate.versions, "remote_latest", boom)
    res = autoupdate.run(tmp_path)
    assert res["mode"] == "off" and res["checked"] is False


def test_panel_binary_is_never_auto_updated(tmp_path: Path, monkeypatch):
    """DOKTRİN: panel ikilisi otomatik güncellenmez (ölçülmüş self-update olayı)."""
    assert "juggler" not in autoupdate.AUTO_AGENTS
    res = autoupdate.apply_update(tmp_path, "juggler")
    assert res["ok"] is False and "elle" in res["detail"]


def test_run_applies_only_auto_agents(tmp_path: Path, monkeypatch):
    updates = [
        {"name": "opencode", "local": "1.0.0", "latest": "1.1.0", "auto": True},
        {"name": "juggler", "local": "v0.5.0", "latest": "0.6.0", "auto": False},
    ]
    monkeypatch.setattr(autoupdate, "find_updates", lambda _r: updates)
    applied: list[str] = []

    def fake_apply(_root, name, **_kw):
        applied.append(name)
        return {"name": name, "ok": True, "detail": "güncellendi"}

    monkeypatch.setattr(autoupdate, "apply_update", fake_apply)
    res = autoupdate.run(tmp_path, force=True)

    assert applied == ["opencode"], "yalniz otomatik listesindekiler kurulmali"
    assert [u["name"] for u in res["updates"]] == ["juggler"], "kalan is bildirilmeli"
    lines = " ".join(autoupdate.summary_lines(res))
    assert "otomatik KURULMAZ" in lines


# --- vendor (indirici) --------------------------------------------------------


def test_unzip_strips_single_top_dir(tmp_path: Path):
    archive = tmp_path / "a.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("node-v1/node.exe", "x")
        zf.writestr("node-v1/lib/a.js", "y")
    dst = tmp_path / "out"
    vendor._unzip_flat(archive, dst)
    assert (dst / "node.exe").is_file() and (dst / "lib" / "a.js").is_file()


def test_unzip_keeps_root_when_asked(tmp_path: Path):
    archive = tmp_path / "b.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("cmd/git.exe", "x")
        zf.writestr("usr/bin/sh.exe", "y")
    dst = tmp_path / "git"
    vendor._unzip_flat(archive, dst, strip_top=False)
    assert (dst / "cmd" / "git.exe").is_file() and (dst / "usr" / "bin" / "sh.exe").is_file()


# --- ollama bulut kimliği -----------------------------------------------------


def test_identity_status_reports_missing(tmp_path: Path):
    st = ollama_identity.status(tmp_path)
    assert st["id"] == "auth.ollama" and not st["ok"] and "signin" in st["detail"]


def test_identity_migrates_from_user_home_once(tmp_path: Path, monkeypatch):
    """ÖLÇÜLDÜ: anahtar depo dışında kalırsa taşınan klasörde bulut modeli
    `Unauthorized` döner. İlk açılışta bir kez depoya alınır."""
    fake_home = tmp_path / "kullanici"
    (fake_home / ".ollama").mkdir(parents=True)
    (fake_home / ".ollama" / "id_ed25519").write_text("OZEL-ANAHTAR", encoding="utf-8")
    (fake_home / ".ollama" / "id_ed25519.pub").write_text("acik", encoding="utf-8")
    monkeypatch.setattr(ollama_identity.Path, "home", staticmethod(lambda: fake_home))

    root = tmp_path / "repo"
    root.mkdir()
    res = ollama_identity.migrate(root)
    assert res["ok"] and res["moved"]
    assert ollama_identity.has_identity(root)
    assert ollama_identity.status(root)["portable"]


def test_identity_never_overwrites_carried_key(tmp_path: Path, monkeypatch):
    """Taşınan arşivin kimliği, açıldığı makinenin kimliğiyle EZİLMEMELİ."""
    fake_home = tmp_path / "kullanici"
    (fake_home / ".ollama").mkdir(parents=True)
    (fake_home / ".ollama" / "id_ed25519").write_text("YENI-MAKINE", encoding="utf-8")
    monkeypatch.setattr(ollama_identity.Path, "home", staticmethod(lambda: fake_home))

    root = tmp_path / "repo"
    keydir = ollama_identity.repo_key_dir(root)
    keydir.mkdir(parents=True)
    (keydir / "id_ed25519").write_text("TASINAN", encoding="utf-8")

    res = ollama_identity.migrate(root)
    assert res["moved"] is False
    assert (keydir / "id_ed25519").read_text(encoding="utf-8") == "TASINAN"


@pytest.mark.skipif(not IS_WIN, reason="sarmalayıcılar Windows'a özgü")
def test_ensure_ollama_points_home_into_repo(tmp_path: Path):
    _stub_tree(tmp_path)
    wrappers.generate(tmp_path)
    text = (tmp_path / "tools" / "agents" / "ensure-ollama.cmd").read_text(encoding="ascii")
    assert 'set "USERPROFILE=%ROOT%\\tools\\ollama\\home"' in text
    assert 'set "HOME=%ROOT%\\tools\\ollama\\home"' in text


# --- paketleme: istege bagli agir yukler --------------------------------------


def test_optional_report_measures_ollama_lib(tmp_path: Path):
    lib = tmp_path / "tools" / "ollama" / "lib"
    lib.mkdir(parents=True)
    (lib / "runner.bin").write_bytes(b"x" * 1024)

    (only,) = package.optional_report(tmp_path, ["ollama-lib"])
    assert only["exists"] and only["size"] == 1024
    assert "bulut" in only["safe_when"] and "SETUP.cmd" in only["restore"]


def test_optional_report_handles_absent_path(tmp_path: Path):
    (only,) = package.optional_report(tmp_path, ["ollama-lib"])
    assert not only["exists"] and only["size"] == 0


def test_archiver_search_does_not_assume_c_drive(tmp_path: Path, monkeypatch):
    """ÖLÇÜLDÜ: WinRAR bu makinede `D:\\Program Files` altındaydı; yalnız C:'ye
    bakan arama "RAR yazamam" diyordu (yanlış cevap, aracın kendisi kuruluydu)."""
    d_drive = tmp_path / "D"
    rar = d_drive / "Program Files" / "WinRAR" / "Rar.exe"
    rar.parent.mkdir(parents=True)
    rar.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(package, "_fixed_drives", lambda: [tmp_path / "C", d_drive])
    monkeypatch.setattr(package.shutil, "which", lambda _n: None)

    found = package.find_archiver("rar")
    assert found and found[0] == rar


def test_archiver_preference_follows_target_extension(tmp_path: Path, monkeypatch):
    """.rar istendiğinde RAR aracı öne alınmalı; aksi hâlde 7-Zip yakalanır ve
    RAR yazamadığı için iş 3-4 GB'lik bir uğraşın SONUNDA patlar."""
    drive = tmp_path / "C"
    for rel in (r"WinRAR\Rar.exe", r"7-Zip\7z.exe"):
        p = drive / "Program Files" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("stub", encoding="utf-8")
    monkeypatch.setattr(package, "_fixed_drives", lambda: [drive])
    monkeypatch.setattr(package.shutil, "which", lambda _n: None)

    assert package.find_archiver("rar")[0].name == "Rar.exe"
    assert package.find_archiver("7z")[0].name == "7z.exe"


def test_7zip_refuses_rar_target_early(tmp_path: Path, monkeypatch):
    """7-Zip RAR yazamaz (`System ERROR: Not implemented`) — bunu ÖNCEDEN söyle."""
    fake_7z = tmp_path / "7z.exe"
    fake_7z.write_text("stub", encoding="utf-8")
    monkeypatch.setattr(package, "find_archiver", lambda prefer="": (fake_7z, ["a"]))

    res = package.make_archive(tmp_path, tmp_path / "cikti.rar", [])
    assert res["ok"] is False and "WinRAR" in res["detail"] and ".7z" in res["detail"]


def test_exclude_args_differ_per_archiver():
    """WinRAR ve 7-Zip dışlamayı farklı yazar; karıştırmak sessizce ETKİSİZ kalır."""
    assert package.exclude_args("7z.exe", ["tools/ollama/lib"]) == [r"-x!tools\ollama\lib"]
    assert package.exclude_args("Rar.exe", ["tools/ollama/lib"]) == [r"-xtools\ollama\lib\*"]


def test_prepare_reports_optional_without_deleting(tmp_path: Path, monkeypatch):
    """--bulut varsayılan olarak SİLMEZ; yalnız arşiv dışında bırakır."""
    lib = tmp_path / "tools" / "ollama" / "lib"
    lib.mkdir(parents=True)
    (lib / "runner.bin").write_bytes(b"x")
    monkeypatch.setattr(package.processes, "juggler_running", lambda _r: False)
    monkeypatch.setattr(package.processes, "stray", lambda _r: [])

    rep = package.prepare(tmp_path, do_slim=False, drop=["ollama-lib"])
    assert rep["optional"][0]["exists"]
    assert lib.is_dir(), "klasor --sil verilmeden silinmemeli"


def test_mingit_gets_a_bash_named_copy(tmp_path: Path):
    """MinGit yalnız sh.exe gönderir; sh.exe ile bash.exe AYNI ikilidir (ölçüldü)."""
    d = tmp_path / "git"
    (d / "usr" / "bin").mkdir(parents=True)
    (d / "usr" / "bin" / "sh.exe").write_bytes(b"bash-ikilisi")
    made = vendor._ensure_bash_name(d)
    assert made and made.name == "bash.exe"
    assert made.read_bytes() == b"bash-ikilisi"
    assert (d / "usr" / "bin" / "sh.exe").is_file(), "sh.exe yerinde kalmali"

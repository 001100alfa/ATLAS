"""ATLAS Juggler profili testleri.

Korunan sözleşme tek cümleyle: **Juggler klasörü silinip yeniden kurulduğunda
ATLAS tarafı ayakta kalmalı.** Bunu bozan üç şey vardır ve üçü de burada
sınanır — kayıtların depo dışını göstermesi, senkronun yabancı kayıtları
silmesi, kurulu kopyanın kaynaktan sapması.

Gerçek Juggler ikilisi veya ağ gerektirmez.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.juggler_profile import sync as profile


def _make_profile(root: Path, mcp: dict | None = None) -> None:
    """Küçük ama gerçek bir profil iskeleti kurar."""
    prof = root / "juggler-profile"
    ext = prof / "extensions" / "atlas-engineering"
    ext.mkdir(parents=True)
    (ext / "juggler.extension.json").write_text('{"version":"0.1.0"}', encoding="utf-8")
    (ext / "lib").mkdir()
    (ext / "lib" / "atlas.js").write_text("// atlas", encoding="utf-8")
    (prof / "commands").mkdir()
    (prof / "commands" / "README.md").write_text("not", encoding="utf-8")
    (prof / "commands" / "hello-command-type.js").write_text("// hello", encoding="utf-8")
    (prof / "mcp").mkdir()
    (prof / "mcp" / "servers.json").write_text(
        json.dumps(mcp if mcp is not None else {"mcpServers": {}}), encoding="utf-8"
    )
    (prof / "profile.json").write_text(
        json.dumps(
            {
                "home": "home",
                "install": [
                    {"source": "extensions", "target": "extensions", "kind": "tree"},
                    {"source": "commands", "target": "commands", "kind": "tree"},
                ],
                "migrateFromUserHome": ["credentials.json"],
            }
        ),
        encoding="utf-8",
    )


def _no_agents(monkeypatch) -> None:
    """ACP üretimini kapatır — testler dosya düzenine odaklansın."""
    monkeypatch.setattr(profile, "_atlas_agent_entries", lambda _root: {})


def _fake_agents(monkeypatch, root: Path, names: tuple[str, ...] = ("goose",)) -> dict:
    entries = {
        n: {"command": str(root / "tools" / "agents" / f"{n}.cmd"), "args": ["acp"], "env": {}}
        for n in names
    }
    monkeypatch.setattr(profile, "_atlas_agent_entries", lambda _root: entries)
    monkeypatch.setattr(profile, "agent_specs", lambda _root=None: dict.fromkeys(names, {}))
    return entries


# --- kurulum -----------------------------------------------------------------


def test_sync_installs_trees_and_skips_readme(tmp_path: Path, monkeypatch):
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")

    r = profile.sync(tmp_path)
    home = tmp_path / "juggler-profile" / "home"
    assert r["ok"] is True
    assert (home / "extensions" / "atlas-engineering" / "lib" / "atlas.js").is_file()
    assert (home / "commands" / "hello-command-type.js").is_file()
    # Klasörü anlatan README Juggler'a kurulmaz.
    assert not (home / "commands" / "README.md").exists()


def test_sync_is_idempotent(tmp_path: Path, monkeypatch):
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")

    first = profile.sync(tmp_path)
    second = profile.sync(tmp_path)
    assert first["first_run"] is True and second["first_run"] is False
    assert second["ok"] is True
    assert profile.verify(tmp_path)["ok"] is True


def test_missing_profile_dir_is_reported(tmp_path: Path):
    r = profile.sync(tmp_path)
    assert r["ok"] is False
    assert "Profil klasörü yok" in r["log"][0]


# --- ilk kurulumda taşıma ----------------------------------------------------


def test_first_run_migrates_user_state(tmp_path: Path, monkeypatch):
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    legacy = tmp_path / "userhome" / ".juggler"
    legacy.mkdir(parents=True)
    (legacy / "credentials.json").write_text('{"token":"abc"}', encoding="utf-8")
    monkeypatch.setattr(profile, "user_home_juggler", lambda: legacy)

    profile.sync(tmp_path)
    moved = tmp_path / "juggler-profile" / "home" / "credentials.json"
    assert moved.is_file(), "kimlik bilgisi taşınmazsa kullanıcı yeniden giriş yapmak zorunda kalır"
    assert legacy.joinpath("credentials.json").is_file(), "kaynak dizine dokunulmamalı"


def test_migration_does_not_overwrite_existing(tmp_path: Path, monkeypatch):
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    legacy = tmp_path / "userhome" / ".juggler"
    legacy.mkdir(parents=True)
    (legacy / "credentials.json").write_text('{"token":"eski"}', encoding="utf-8")
    monkeypatch.setattr(profile, "user_home_juggler", lambda: legacy)
    home = tmp_path / "juggler-profile" / "home"
    home.mkdir(parents=True)
    (home / "credentials.json").write_text('{"token":"yeni"}', encoding="utf-8")

    profile.migrate_user_state(tmp_path, [])
    assert json.loads((home / "credentials.json").read_text(encoding="utf-8"))["token"] == "yeni"


# --- ACP birleştirme ---------------------------------------------------------


def test_merge_acp_preserves_foreign_agents(tmp_path: Path):
    path = tmp_path / "acp.json"
    path.write_text(
        json.dumps({"acpAgents": {"baskaAjan": {"command": "X"}, "goose": {"command": "ESKI"}}}),
        encoding="utf-8",
    )
    entries = {"goose": {"command": "YENI", "args": [], "env": {}}}
    log: list[str] = []
    doc = profile.merge_acp(path, entries, log, "test")

    assert doc["acpAgents"]["baskaAjan"] == {"command": "X"}, "yabancı kayıt silinmemeli"
    assert doc["acpAgents"]["goose"]["command"] == "YENI", "ATLAS ajanı tazelenmeli"
    assert "1 kayıt tazelendi" in log[0]


def test_merge_acp_repairs_broken_json(tmp_path: Path):
    path = tmp_path / "acp.json"
    path.write_text("{ bozuk", encoding="utf-8")
    doc = profile.merge_acp(path, {"goose": {"command": "Y"}}, [], "test")
    assert doc["acpAgents"]["goose"]["command"] == "Y"


def test_sync_writes_all_three_scopes(tmp_path: Path, monkeypatch):
    """Kullanıcı + proje her zaman; eski global YALNIZ zaten varsa."""
    _make_profile(tmp_path)
    _fake_agents(monkeypatch, tmp_path)
    legacy_dir = tmp_path / "userhome" / ".juggler"
    legacy_dir.mkdir(parents=True)
    legacy = legacy_dir / "acp.json"
    legacy.write_text(json.dumps({"acpAgents": {"goose": {"command": "ESKI"}}}), encoding="utf-8")
    monkeypatch.setattr(profile, "user_home_juggler", lambda: legacy_dir)

    profile.sync(tmp_path)
    home = tmp_path / "juggler-profile" / "home"
    for p in (home / "acp.json", tmp_path / ".juggler" / "acp.json", legacy):
        agents = json.loads(p.read_text(encoding="utf-8"))["acpAgents"]
        assert "goose" in agents
        assert str(tmp_path) in agents["goose"]["command"], f"{p} depo içini göstermeli"


def test_legacy_acp_not_created_when_absent(tmp_path: Path, monkeypatch):
    """Kullanıcının hiç dokunmadığı bir yere durum yazılmaz."""
    _make_profile(tmp_path)
    _fake_agents(monkeypatch, tmp_path)
    legacy_dir = tmp_path / "userhome" / ".juggler"
    monkeypatch.setattr(profile, "user_home_juggler", lambda: legacy_dir)

    profile.sync(tmp_path)
    assert not (legacy_dir / "acp.json").exists()


# --- MCP ---------------------------------------------------------------------


def test_mcp_placeholder_is_expanded_and_merged(tmp_path: Path, monkeypatch):
    _make_profile(
        tmp_path,
        mcp={"mcpServers": {"atlas-demo": {"command": "${ATLAS_HOME}/atlas.cmd", "args": ["x"]}}},
    )
    _no_agents(monkeypatch)
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")
    home = tmp_path / "juggler-profile" / "home"
    home.mkdir(parents=True)
    (home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"yabanci": {"command": "Z"}}}), encoding="utf-8"
    )

    profile.sync(tmp_path)
    servers = json.loads((home / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    assert servers["yabanci"] == {"command": "Z"}, "yabancı MCP sunucusu korunmalı"
    assert "${ATLAS_HOME}" not in servers["atlas-demo"]["command"]
    assert str(tmp_path) in servers["atlas-demo"]["command"]


# --- doğrulama ---------------------------------------------------------------


def test_verify_flags_registration_outside_repo(tmp_path: Path, monkeypatch):
    """Asıl regresyon koruması: bir ATLAS ajanı depo dışını gösteriyorsa yakala."""
    _make_profile(tmp_path)
    _fake_agents(monkeypatch, tmp_path)
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")
    profile.sync(tmp_path)
    assert profile.verify(tmp_path)["ok"] is True

    # Kayıt Juggler ağacının içini göstermeye başlasın (güncelleme/taşıma sonrası hâli).
    proj = tmp_path / ".juggler" / "acp.json"
    doc = json.loads(proj.read_text(encoding="utf-8"))
    doc["acpAgents"]["goose"]["command"] = r"C:\Baska\juggler\scripts\goose.cmd"
    proj.write_text(json.dumps(doc), encoding="utf-8")

    res = profile.verify(tmp_path)
    assert res["ok"] is False
    assert any("goose" in e for e in res["external"])


def test_verify_flags_stale_extension(tmp_path: Path, monkeypatch):
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")
    profile.sync(tmp_path)

    # Kaynak değişti ama senkron yapılmadı.
    src = tmp_path / "juggler-profile" / "extensions" / "atlas-engineering" / "lib" / "atlas.js"
    src.write_text("// atlas v2 — daha uzun içerik", encoding="utf-8")

    res = profile.verify(tmp_path)
    assert res["ok"] is False
    assert any("kaynaktan farklı" in s for s in res["stale"])
    profile.sync(tmp_path)
    assert profile.verify(tmp_path)["ok"] is True


def test_verify_without_profile_dir(tmp_path: Path):
    res = profile.verify(tmp_path)
    assert res["ok"] is False
    assert res["problems"]

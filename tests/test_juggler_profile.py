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
    # Gercek profil gibi: otomatik guncelleyici kapali (yoksa verify sorun bildirir).
    (prof / "settings.json").write_text(json.dumps({"updates": {"mode": "off"}}), encoding="utf-8")
    (prof / "profile.json").write_text(
        json.dumps(
            {
                "home": "home",
                "install": [
                    {"source": "extensions", "target": "extensions", "kind": "tree"},
                    {"source": "commands", "target": "commands", "kind": "tree"},
                    {
                        "source": "settings.json",
                        "target": "settings.json",
                        "kind": "merge-json-toplevel",
                    },
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


# --- otomatik güncelleyiciyi kapatma -----------------------------------------


def test_settings_merge_only_touches_owned_keys(tmp_path: Path, monkeypatch):
    """ATLAS yalnız sahiplendiği bölümü dayatır; kullanıcının ayarları kalır."""
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")
    prof = tmp_path / "juggler-profile"
    (prof / "settings.json").write_text(
        json.dumps({"_comment": "yorum", "updates": {"mode": "off"}}), encoding="utf-8"
    )
    cfg = json.loads((prof / "profile.json").read_text(encoding="utf-8"))
    cfg["install"].append(
        {"source": "settings.json", "target": "settings.json", "kind": "merge-json-toplevel"}
    )
    (prof / "profile.json").write_text(json.dumps(cfg), encoding="utf-8")

    home = prof / "home"
    home.mkdir(parents=True)
    (home / "settings.json").write_text(
        json.dumps({"connectivity": {"lanOnLaunch": True}, "updates": {"mode": "automatic"}}),
        encoding="utf-8",
    )

    profile.sync(tmp_path)
    doc = json.loads((home / "settings.json").read_text(encoding="utf-8"))
    assert doc["updates"] == {"mode": "off"}, "otomatik güncelleyici kapatılmalı"
    assert doc["connectivity"] == {"lanOnLaunch": True}, "diğer bölümlere dokunulmamalı"
    assert "_comment" not in doc, "yorum anahtarı kurulmamalı"


def test_verify_flags_enabled_autoupdate(tmp_path: Path, monkeypatch):
    """Açık otomatik güncelleyici bir SORUN olarak raporlanır."""
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")
    profile.sync(tmp_path)
    home = tmp_path / "juggler-profile" / "home"
    assert profile.verify(tmp_path)["update_mode"] == "off"

    # Ayar "automatic"e döndürülürse (panel veya kullanıcı) sorun bildirilir.
    (home / "settings.json").write_text(
        json.dumps({"updates": {"mode": "automatic"}}), encoding="utf-8"
    )
    res = profile.verify(tmp_path)
    assert res["update_mode"] == "automatic"
    assert res["ok"] is False
    assert any("otomatik güncelleyici" in x.lower() for x in res["problems"])

    # Dosya hiç yoksa da varsayılan "automatic"tir — sessiz geçilmez.
    (home / "settings.json").unlink()
    assert profile.verify(tmp_path)["update_mode"] == "automatic"


def test_legacy_autoupdate_disabled_only_when_dir_exists(tmp_path: Path, monkeypatch):
    """Panel başlatıcısız açılabilir; eski konumdaki ayar da kapatılır."""
    _make_profile(tmp_path)
    _no_agents(monkeypatch)
    prof = tmp_path / "juggler-profile"
    (prof / "settings.json").write_text(json.dumps({"updates": {"mode": "off"}}), encoding="utf-8")

    # (a) dizin yoksa oluşturulmaz
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "yok")
    profile.sync(tmp_path)
    assert not (tmp_path / "yok" / "settings.json").exists()

    # (b) dizin varsa yalnız updates bölümü yazılır
    legacy = tmp_path / "userhome" / ".juggler"
    legacy.mkdir(parents=True)
    (legacy / "settings.json").write_text(
        json.dumps({"connectivity": {"lanOnLaunch": True}}), encoding="utf-8"
    )
    monkeypatch.setattr(profile, "user_home_juggler", lambda: legacy)
    profile.sync(tmp_path)
    doc = json.loads((legacy / "settings.json").read_text(encoding="utf-8"))
    assert doc["updates"] == {"mode": "off"}
    assert doc["connectivity"] == {"lanOnLaunch": True}


# --- devre dışı ajanlar -------------------------------------------------------


def test_disabled_agent_is_not_registered_and_existing_entry_removed(tmp_path: Path, monkeypatch):
    """Devre dışı ajan panele yazılmaz; daha önce yazılmışsa kaydı KALDIRILIR.

    Kaydı elle silmek yetmez — senkron her açılışta kurulu ajanları yeniden
    yazacağı için ajan geri gelirdi. Bu yüzden liste profilin kaynağında durur.
    """
    _make_profile(tmp_path)
    prof = tmp_path / "juggler-profile"
    cfg = json.loads((prof / "profile.json").read_text(encoding="utf-8"))
    cfg["disabledAgents"] = ["kimi"]
    (prof / "profile.json").write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")

    # Hem etkin hem devre dışı ajan "kurulu" görünsün.
    entries = {
        n: {"command": str(tmp_path / "tools" / "agents" / f"{n}.cmd"), "args": [], "env": {}}
        for n in ("goose", "kimi")
    }
    monkeypatch.setattr(profile, "agent_specs", lambda _r=None: dict.fromkeys(entries, {}))
    monkeypatch.setattr(
        profile,
        "_atlas_agent_entries",
        lambda r: {k: v for k, v in entries.items() if k not in profile.disabled_agents(r)},
    )

    proj = tmp_path / ".juggler" / "acp.json"
    proj.parent.mkdir(parents=True)
    proj.write_text(json.dumps({"acpAgents": {"kimi": {"command": "ESKI"}}}), encoding="utf-8")

    res = profile.sync(tmp_path)
    assert res["disabled"] == ["kimi"]
    agents = json.loads(proj.read_text(encoding="utf-8"))["acpAgents"]
    assert "goose" in agents
    assert "kimi" not in agents, "devre dışı ajanın eski kaydı kaldırılmalı"


def test_verify_flags_lingering_disabled_entry(tmp_path: Path, monkeypatch):
    """Devre dışı ajanın kaydı bir yolla geri gelirse denetim bunu söyler."""
    _make_profile(tmp_path)
    prof = tmp_path / "juggler-profile"
    cfg = json.loads((prof / "profile.json").read_text(encoding="utf-8"))
    cfg["disabledAgents"] = ["kimi"]
    (prof / "profile.json").write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setattr(profile, "user_home_juggler", lambda: tmp_path / "nohome")
    _no_agents(monkeypatch)
    monkeypatch.setattr(profile, "agent_specs", lambda _r=None: {"kimi": {}})

    profile.sync(tmp_path)
    assert profile.verify(tmp_path)["ok"] is True

    home = tmp_path / "juggler-profile" / "home"
    (home / "acp.json").write_text(
        json.dumps({"acpAgents": {"kimi": {"command": "X"}}}), encoding="utf-8"
    )
    res = profile.verify(tmp_path)
    assert res["ok"] is False
    assert any("Devre dışı" in p for p in res["problems"])

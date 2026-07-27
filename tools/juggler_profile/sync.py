"""ATLAS Juggler profilini kurar/tazeler (yalnız stdlib).

Neden var: Juggler'ın kullanıcı durumu normalde `~/.juggler`'dadır ve oradaki
kayıtlar kolayca Juggler ağacının içini gösterir hâle gelir. O ağaç silinip
yeni sürüm kurulduğunda ATLAS'a ait ne varsa kopar. Bu modül tersini kurar:
ATLAS'ın Juggler'a kattığı her şey depo içindeki `juggler-profile/` altında
durur, `JUGGLER_CONFIG_DIR` ile Juggler oraya bakar. Juggler klasörü silinebilir.

Kurallar:

* **Idempotent** — iki kez çalıştırmak zarar vermez.
* **Yıkıcı değil** — birleştirilen JSON'larda profil dışından gelen kayıtlar
  (yabancı ACP ajanı, yabancı MCP sunucusu) korunur; yalnız ATLAS'ınkiler
  tazelenir.
* **Tek yön** — kaynak (`juggler-profile/*`) → çalışma dizini
  (`juggler-profile/home/`). Ters yönde kopyalama yoktur.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from tools.setup_gui import wrappers
from tools.setup_gui.detect import agent_specs, project_root


def profile_dir(root: Path) -> Path:
    return root / "juggler-profile"


def home_dir(root: Path) -> Path:
    """`JUGGLER_CONFIG_DIR`in göstereceği dizin — Juggler'ın tüm kullanıcı durumu."""
    return profile_dir(root) / "home"


def user_home_juggler() -> Path:
    """Juggler'ın varsayılan (profil kullanılmadığındaki) durum dizini."""
    return Path.home() / ".juggler"


def load_profile(root: Path) -> dict:
    f = profile_dir(root) / "profile.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _read_json(path: Path) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return doc if isinstance(doc, dict) else {}


def _write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _copy_tree(src: Path, dst: Path, log: list[str]) -> int:
    """Kaynak ağacı hedefe kopyalar (varsa üzerine yazar). Kopyalanan dosya sayısı."""
    if not src.is_dir():
        return 0
    n = 0
    for item in sorted(src.iterdir()):
        if item.name == "README.md" and item.parent == src:
            continue  # klasörü anlatan not; Juggler'a kurulmaz
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
            n += sum(1 for _ in item.rglob("*") if _.is_file())
        else:
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            n += 1
    if n:
        log.append(f"  {src.name}/ → {dst} ({n} dosya)")
    return n


# --- ilk kurulumda taşıma -----------------------------------------------------


def migrate_user_state(root: Path, log: list[str]) -> list[str]:
    """`home/` ilk kez kuruluyorsa ~/.juggler'daki taşınabilir durumu kopyalar.

    Kimlik bilgileri ve model tercihleri taşınmazsa kullanıcı profile geçtiği an
    panelde yeniden giriş yapmak zorunda kalır. Kaynak dizine DOKUNULMAZ.
    """
    home = home_dir(root)
    src = user_home_juggler()
    moved: list[str] = []
    if not src.is_dir():
        return moved
    for name in load_profile(root).get("migrateFromUserHome", []):
        s, d = src / name, home / name
        if s.is_file() and not d.exists():
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            moved.append(name)
    if moved:
        log.append(f"  ~/.juggler'dan taşındı: {', '.join(moved)}")
    return moved


# --- ACP ajanları -------------------------------------------------------------


def _atlas_agent_entries(root: Path) -> dict:
    """ATLAS ajanlarının GERÇEK kurulumdan üretilmiş acp.json girdileri.

    Şablon tutulmaz: yollar makineye özeldir (node konumu, sarmalayıcı yolu),
    şablonla gerçek arasındaki sapma tam da paneli bozan şeydir.
    """
    wrappers.generate(root)
    specs = agent_specs(root)
    entries: dict[str, dict] = {}
    for name, spec in specs.items():
        if not Path(spec["bin"]).is_file():
            continue
        if wrappers.wrapper_path(root, name).is_file():
            entries[name] = wrappers.wrapper_entry(root, name, spec)
    return entries


def _snapshot(d: Path) -> dict[str, int]:
    """Bir ağacın kaba parmak izi: göreli yol → boyut. Kaynak ↔ kurulu farkı için."""
    return {p.relative_to(d).as_posix(): p.stat().st_size for p in d.rglob("*") if p.is_file()}


def merge_acp(path: Path, entries: dict, log: list[str], label: str) -> dict:
    """ATLAS ajanlarını acp.json'a yazar, yabancı kayıtları korur.

    Tek istisna: yabancı bir kayıt ATLAS'ın sahiplendiği bir ajan adını
    kullanıyorsa üzerine yazılır — panelde tek bir "goose" olabilir ve onun
    ATLAS sürümü olmasını istiyoruz.
    """
    doc = _read_json(path)
    agents = dict(doc.get("acpAgents") or {})
    replaced = [n for n in entries if n in agents and agents[n] != entries[n]]
    agents.update(entries)
    doc["acpAgents"] = agents
    _write_json(path, doc)
    log.append(
        f"  ACP ({label}): {len(entries)} ATLAS ajanı yazıldı"
        + (f", {len(replaced)} kayıt tazelendi" if replaced else "")
        + f" → {path}"
    )
    return doc


def merge_toplevel_json(root: Path, source: str, target: str, log: list[str]) -> list[str]:
    """Profildeki bir JSON'u hedefe ÜST DÜZEY ANAHTAR bazında birleştirir.

    Kullanımı `settings.json` içindir: ATLAS yalnız sahiplendiği bölümü dayatır
    (ör. `updates`), kullanıcının/panelin diğer bölümlerine (`connectivity`,
    `sandbox`, …) dokunmaz. `_` ile başlayan anahtarlar yorumdur, kurulmaz.
    """
    src = profile_dir(root) / source
    if not src.is_file():
        return []
    wanted = {k: v for k, v in _read_json(src).items() if not k.startswith("_")}
    if not wanted:
        return []
    dst = home_dir(root) / target
    doc = _read_json(dst)
    doc.update(wanted)
    _write_json(dst, doc)
    keys = sorted(wanted)
    log.append(f"  {target}: {', '.join(keys)} → {dst}")
    return keys


# --- MCP ----------------------------------------------------------------------


def merge_mcp(root: Path, log: list[str]) -> int:
    """Profildeki MCP sunucularını `home/mcp.json`a birleştirir."""
    src = profile_dir(root) / "mcp" / "servers.json"
    if not src.is_file():
        return 0
    wanted = _read_json(src).get("mcpServers") or {}
    # ${ATLAS_HOME} yer tutucusu depo köküyle değiştirilir (taşınabilirlik).
    text = json.dumps(wanted, ensure_ascii=False).replace(
        "${ATLAS_HOME}", str(root).replace("\\", "\\\\")
    )
    wanted = json.loads(text)

    dst = home_dir(root) / "mcp.json"
    doc = _read_json(dst)
    servers = dict(doc.get("mcpServers") or {})
    servers.update(wanted)
    doc["mcpServers"] = servers
    _write_json(dst, doc)
    if wanted:
        log.append(f"  MCP: {len(wanted)} sunucu → {dst}")
    return len(wanted)


# --- ana akış -----------------------------------------------------------------


def sync(root: Path | None = None) -> dict:
    """Profili kurar/tazeler. Dönüş: {ok, home, log, agents, mcp}."""
    root = root or project_root()
    prof, home = profile_dir(root), home_dir(root)
    log: list[str] = []
    if not prof.is_dir():
        return {"ok": False, "log": [f"Profil klasörü yok: {prof}"], "home": str(home)}

    first_run = not home.is_dir()
    home.mkdir(parents=True, exist_ok=True)
    log.append(f"Profil: {prof}")
    log.append(f"Çalışma dizini (JUGGLER_CONFIG_DIR): {home}")
    if first_run:
        log.append("  ilk kurulum — kullanıcı durumu taşınıyor")
        migrate_user_state(root, log)

    for spec in load_profile(root).get("install", []):
        if spec.get("kind") == "tree":
            _copy_tree(prof / spec["source"], home / spec["target"], log)
        elif spec.get("kind") == "merge-json-toplevel":
            merge_toplevel_json(root, spec["source"], spec["target"], log)
    mcp_n = merge_mcp(root, log)

    entries = _atlas_agent_entries(root)
    merge_acp(home / "acp.json", entries, log, "kullanıcı")
    merge_acp(root / ".juggler" / "acp.json", entries, log, "proje")

    # Eski global kayıt (~/.juggler/acp.json) da onarılır — VARSA. Başlatıcılar
    # profili gösterse de Juggler elle (başlatıcısız) açılabilir; o durumda okunan
    # dosya budur ve içindeki ATLAS ajanları Juggler ağacını gösteriyor olabilir.
    # Yoksa oluşturulmaz: kullanıcının hiç dokunmadığı bir yere durum yazmayız.
    legacy = user_home_juggler() / "acp.json"
    if legacy.is_file():
        merge_acp(legacy, entries, log, "eski global")

    # Otomatik güncelleyici eski konumda da kapatılır. Gerekçe: panel ATLAS
    # başlatıcıları DIŞINDAN (doğrudan tools/juggler/juggler.exe ile) açılırsa
    # ayarları oradan okur ve otomatik güncelleme ATLAS'ın ikilisini yerinde
    # değiştirip yerel derlemeyi siler — 2026-07-27'de yaşandı. Yalnız `updates`
    # bölümü yazılır; kullanıcının diğer ayarlarına dokunulmaz. Manuel "güncelleme
    # denetle" kapanmaz.
    if user_home_juggler().is_dir():
        wanted = {
            k: v
            for k, v in _read_json(profile_dir(root) / "settings.json").items()
            if k == "updates"
        }
        if wanted:
            p = user_home_juggler() / "settings.json"
            doc = _read_json(p)
            if doc.get("updates") != wanted["updates"]:
                doc.update(wanted)
                _write_json(p, doc)
                log.append(f"  settings.json (eski global): otomatik güncelleme kapatıldı → {p}")

    log.append("Tamam — Juggler bir sonraki açılışta bu profili kullanır.")
    return {
        "ok": True,
        "home": str(home),
        "log": log,
        "agents": sorted(entries),
        "mcp": mcp_n,
        "first_run": first_run,
    }


def verify(root: Path | None = None) -> dict:
    """Yazmadan denetler: profil kurulu mu, kayıtlar Juggler ağacını mı gösteriyor?

    Asıl soruyu yanıtlar: "Juggler klasörünü silsem ne kırılır?"
    """
    root = root or project_root()
    home = home_dir(root)
    prof = profile_dir(root)
    problems: list[str] = []

    if not prof.is_dir():
        problems.append(f"Profil klasörü yok: {prof}")
        return {"ok": False, "problems": problems, "home": str(home), "stale": [], "external": []}

    if not home.is_dir():
        problems.append("Profil henüz kurulmadı (home/ yok) — juggler-profile_Sync.cmd çalıştırın.")

    # Kaynak ↔ kurulu eklenti karşılaştırması (sürüm ve dosya sayısı).
    stale: list[str] = []
    for ext in sorted((prof / "extensions").glob("*")):
        if not ext.is_dir():
            continue
        installed = home / "extensions" / ext.name
        if not installed.is_dir():
            stale.append(f"{ext.name}: kurulu değil")
            continue
        if _snapshot(ext) != _snapshot(installed):
            stale.append(f"{ext.name}: kurulu kopya kaynaktan farklı")

    # ATLAS ajanları hâlâ Juggler ağacının içini mi gösteriyor?
    external: list[str] = []
    owned = set(agent_specs(root))
    for label, path in (
        ("kullanıcı", home / "acp.json"),
        ("proje", root / ".juggler" / "acp.json"),
        ("eski global", user_home_juggler() / "acp.json"),
    ):
        for name, cfg in (_read_json(path).get("acpAgents") or {}).items():
            if name not in owned:
                continue
            cmd = str((cfg or {}).get("command") or "")
            try:
                inside_atlas = Path(cmd).resolve().is_relative_to(root.resolve())
            except (OSError, ValueError):
                inside_atlas = False
            if cmd and not inside_atlas:
                external.append(f"{label}/{name} → {cmd}")

    # Panelin otomatik güncelleyicisi kapalı mı? Açıkken çalışan ikiliyi yerinde
    # değiştirir ve yerel derlemeyi (ACP authenticate, childcontain, …) siler —
    # 2026-07-27'de bu makinede yaşandı, bkz. ATLAS DECISIONS.
    settings = _read_json(home / "settings.json")
    update_mode = ((settings.get("updates") or {}).get("mode") or "automatic").lower()
    if update_mode != "off":
        problems.append(
            f"Panelin otomatik güncelleyicisi açık (updates.mode={update_mode}); "
            "çalışan ikiliyi yerinde değiştirip yerel derlemeyi silebilir."
        )

    return {
        "ok": not problems and not stale and not external,
        "problems": problems,
        "stale": stale,
        "external": external,
        "update_mode": update_mode,
        "home": str(home),
    }


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    argv = argv if argv is not None else sys.argv[1:]
    root = project_root()

    if "--verify" in argv:
        r = verify(root)
        print(f"Profil çalışma dizini: {r['home']}")
        for p in r["problems"]:
            print(f"  [SORUN] {p}")
        for s in r["stale"]:
            print(f"  [ESKİ]  {s}")
        for e in r["external"]:
            print(f"  [DIŞ]   ATLAS ajanı depo dışını gösteriyor: {e}")
        print("Profil sağlam." if r["ok"] else "Onarım için: juggler-profile_Sync.cmd")
        return 0 if r["ok"] else 1

    r = sync(root)
    for line in r["log"]:
        print(line)
    if r["ok"] and r["agents"]:
        print(f"ACP ajanları: {', '.join(r['agents'])}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

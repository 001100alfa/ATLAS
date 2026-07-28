"""Klasör başka bir makineye/yola taşındığında kendini onarır.

SORUN: kurulumun bazı parçaları makineye özgüdür ve sıkıştırılıp taşınınca
geçersizleşir — sarmalayıcılardaki node/git yolları, `acp.json`daki mutlak
sarmalayıcı yolları, Juggler profilinin çalışma dizini. Kullanıcı bunları elle
onarmak zorunda kalırsa "aç ve çalıştır" vaadi çöker.

ÇÖZÜM: her açılışta ucuz bir PARMAK İZİ karşılaştırması yapılır (makine adı +
depo yolu + node/git konumu). Değişmişse makineye özgü ne varsa yeniden
üretilir; değişmemişse hiçbir şey yapılmaz (birkaç milisaniye).

Üretilenler kaynaktan türer, şablondan değil: sarmalayıcılar kurulu ikililere,
ACP kayıtları sarmalayıcılara, profil `juggler-profile/`ye bakar.
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path

from tools.juggler_profile import sync as profile_sync
from tools.setup_gui import connect, wrappers

from . import ollama_identity, runtimes

STATE_REL = (".atlas", "portable", "machine.json")


def state_path(root: Path) -> Path:
    return root.joinpath(*STATE_REL)


def fingerprint(root: Path) -> dict:
    """Yeniden yerleştirmeyi gerektiren her şey — ve fazlası değil."""
    node = runtimes.bundled_node(root) or Path(runtimes.node_exe(root))
    bash = runtimes.git_bash(root)
    return {
        "host": platform.node(),
        "user": os.environ.get("USERNAME", ""),
        "root": str(root.resolve()),
        "node": str(node),
        "bash": str(bash or ""),
    }


def read_state(root: Path) -> dict:
    p = state_path(root)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(root: Path, fp: dict) -> Path:
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(fp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def needs_relocate(root: Path) -> tuple[bool, list[str]]:
    """(gerekli mi, hangi alanlar değişti) — hiç kayıt yoksa gereklidir."""
    old, new = read_state(root), fingerprint(root)
    if not old:
        return True, ["ilk çalıştırma"]
    changed = [k for k, v in new.items() if old.get(k) != v]
    return bool(changed), changed


def relocate(root: Path, force: bool = False) -> dict:
    """Makineye özgü üretilmiş ne varsa tazeler. İdempotent."""
    needed, changed = needs_relocate(root)
    if not needed and not force:
        return {"ok": True, "changed": [], "steps": [], "detail": "Yerleşim güncel."}

    steps: list[dict] = []

    # 1) Sarmalayıcılar — node/git yolları ve ajan ikilileri buradan geçer.
    res = wrappers.generate(root)
    steps.append(
        {
            "step": "sarmalayicilar",
            "ok": bool(res.get("ok")),
            "detail": f"{len(res.get('written') or [])} ajan sarmalayicisi yazildi",
        }
    )

    # 2) ACP kayitlari — panel bunlari okur; mutlak sarmalayici yolu tasiyorlar.
    reg = connect.register_agents(root)
    steps.append(
        {
            "step": "acp-kayit",
            "ok": True,
            "detail": f"{len(reg['written'])} ajan kaydedildi ({', '.join(reg['written'])})",
        }
    )

    # 3) Ollama bulut kimligi — depo disinda kalirsa tasinmaz (bkz. modul).
    ident = ollama_identity.migrate(root)
    if ident["moved"]:
        steps.append({"step": "ollama-kimligi", "ok": True, "detail": ident["detail"]})

    # 4) Juggler profili — eklenti, komutlar, ayarlar, kullanici/proje acp.json.
    try:
        sync = profile_sync.sync(root)
        steps.append(
            {
                "step": "profil",
                "ok": True,
                "detail": f"{len(sync.get('agents') or [])} ajan profile yazildi",
            }
        )
    except Exception as exc:  # profil onarimi tasima icin kritik degil
        steps.append({"step": "profil", "ok": False, "detail": f"atlandi: {exc}"})

    fp = fingerprint(root)
    write_state(root, fp)
    return {
        "ok": all(s["ok"] for s in steps),
        "changed": changed,
        "steps": steps,
        "fingerprint": fp,
        "detail": "Yeni makineye uyarlandi: " + ", ".join(changed) if changed else "Tazelendi.",
    }


def preflight(root: Path) -> list[dict]:
    """Çalıştırmadan önce "elimde ne var?" tablosu — eksikler engel değil, uyarı."""
    out: list[dict] = []
    for rt in runtimes.report(root):
        out.append(
            {
                "id": f"runtime.{rt['name']}",
                "ok": bool(rt["path"]),
                "portable": rt["portable"],
                "detail": rt["path"] or "bulunamadi",
                "needed_by": rt["needed_by"],
            }
        )
    out.append(ollama_identity.status(root))
    # Uzun yol tuzağı: node_modules ağacı derindir, Windows'un 260 karakter
    # sınırı kök yolu uzunsa AÇARKEN vurur (dosyalar sessizce eksik kalır).
    root_len = len(str(root))
    out.append(
        {
            "id": "path.length",
            "ok": root_len <= 60,
            "portable": root_len <= 60,
            "detail": f"kok yolu {root_len} karakter"
            + ("" if root_len <= 60 else " - C:\\ATLAS gibi kisa bir yere acin"),
            "needed_by": "derin node_modules agaci (260 karakter siniri)",
        }
    )
    specs = {
        "juggler": root / "tools" / "juggler" / "juggler.exe",
        "ollama": root / "tools" / "ollama" / "ollama.exe",
    }
    for name, p in specs.items():
        out.append(
            {
                "id": f"bin.{name}",
                "ok": p.is_file(),
                "portable": p.is_file(),
                "detail": str(p) if p.is_file() else "yok",
                "needed_by": "panel" if name == "juggler" else "yerel model ucu",
            }
        )
    return out

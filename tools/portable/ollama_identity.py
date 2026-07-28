"""Ollama bulut kimliğini depo içinde tutar (taşınabilirlik açığıydı).

ÖLÇÜLDÜ (2026-07-28): `ollama signin` kimliği bir anahtar çiftidir ve
`%USERPROFILE%\\.ollama\\id_ed25519` altında durur — yani DEPONUN DIŞINDA.
Klasör başka bir bilgisayara taşındığında o anahtar gelmez; ollama sessizce
YENİ bir anahtar üretir ve bulut modeli ilk istekte `{"error":"Unauthorized"}`
döner. Sonuç: goose ve kimi (modeli bu uçtan alıyorlar) çalışmaz ve kullanıcı
"yine kurulum" yapmak zorunda kalır.

ÇÖZÜM: ollama sunucusunun ev dizini `tools/ollama/home`a çevrilir
(`ensure-ollama.cmd` içinde `USERPROFILE`/`HOME`) ve mevcut anahtar bir kez
oraya taşınır. Kanıt: anahtar kopyalandıktan sonra aynı uç bulut modelinden
yanıt üretti; kopyalanmadan önce `Unauthorized` veriyordu.

GÜVENLİK: bu bir ÖZEL anahtardır ve artık arşive dahildir. Arşivi paylaşan,
ollama hesabına erişimi de paylaşır (aynı kural ajan token'ları için de geçerli,
bkz. docs/TASINABILIR.md).
"""

from __future__ import annotations

import shutil
from pathlib import Path

KEY_NAMES = ("id_ed25519", "id_ed25519.pub")


def repo_home(root: Path) -> Path:
    """Ollama sunucusunun ev dizini olarak kullanılacak depo içi klasör."""
    return root / "tools" / "ollama" / "home"


def repo_key_dir(root: Path) -> Path:
    return repo_home(root) / ".ollama"


def user_key_dir() -> Path:
    return Path.home() / ".ollama"


def has_identity(root: Path) -> bool:
    return (repo_key_dir(root) / "id_ed25519").is_file()


def migrate(root: Path) -> dict:
    """Kullanıcı evindeki kimliği depo içine BİR KEZ kopyalar.

    Depoda zaten kimlik varsa dokunulmaz — taşınan arşivin kimliği, açıldığı
    makinenin kimliğiyle EZİLMEMELİ (o makinede hiç ollama hesabı olmayabilir).
    """
    dst = repo_key_dir(root)
    if has_identity(root):
        return {"ok": True, "moved": False, "detail": "kimlik zaten depo icinde"}
    src = user_key_dir()
    if not (src / "id_ed25519").is_file():
        return {
            "ok": False,
            "moved": False,
            "detail": "kimlik yok - bulut modelleri icin bir kez `ollama signin` gerekir",
        }
    dst.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in KEY_NAMES:
        p = src / name
        if p.is_file():
            shutil.copy2(p, dst / name)
            copied.append(name)
    return {"ok": True, "moved": True, "detail": f"kimlik depoya alindi ({', '.join(copied)})"}


def status(root: Path) -> dict:
    """Preflight satırı: bulut kimliği taşınabilir mi?"""
    ok = has_identity(root)
    return {
        "id": "auth.ollama",
        "ok": ok,
        "portable": ok,
        "detail": str(repo_key_dir(root) / "id_ed25519") if ok else "yok (`ollama signin`)",
        "needed_by": "bulut modelleri (goose, kimi)",
    }

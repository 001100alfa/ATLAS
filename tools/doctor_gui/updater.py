"""Toplu ACP ajan güncelleyicisi — DOCTOR'un "Hepsini güncelle" işlemi.

Yerel sürümü üstakımdan eski her ajanı sırayla günceller, çıktısını canlı akıtır
ve sonda özet basar. Önce artık ajan süreçlerini kapatır (npm/pip yüklemesi
kilitli ikili yüzünden EBUSY ile düşmesin). Idempotent — güncel ajan atlanır,
her adım hatasız bittiğinde bir sonrakine geçilir; bir adım düşse de kalanlar
denenir ve özet fail listesi verir.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.setup_gui.detect import project_root

from . import fixes, processes, versions

# Denetlenecek ACP ajanları — fixes.NPM_PACKAGES + pip/binary olanlar.
_AGENTS: tuple[str, ...] = ("opencode", "kilo", "cline", "kimi", "goose")


def _outdated(root: Path) -> list[str]:
    local = versions.local_versions(root)
    old: list[str] = []
    for name in _AGENTS:
        lv = local.get(name)
        latest = versions.remote_latest(name)
        if lv and latest and versions.is_outdated(lv, latest):
            old.append(name)
    return old


def main() -> int:
    root = project_root()
    old = _outdated(root)
    if not old:
        print("Guncel olmayan ACP ajani yok.")
        return 0

    print(f"Guncelleme sirasi: {', '.join(old)}")

    # Ajan sureclerini kapat; kilitli ikili npm/pip'i EBUSY ile dusurmesin.
    stray = processes.stray(root)
    if stray:
        res = processes.kill([p["pid"] for p in stray])
        killed = len(res.get("killed") or [])
        gone = len(res.get("gone") or [])
        print(
            f"[on-hazirlik] {killed} surec kapatildi"
            + (f", {gone} zaten sonlanmisti" if gone else "")
        )

    failed: list[tuple[str, int]] = []
    for agent in old:
        spec = fixes.job_argv(f"update-{agent}", root)
        if spec is None:
            print(f"[atlanan] {agent}: is tanimsiz (job_argv None)")
            failed.append((agent, -1))
            continue
        argv, title = spec
        print(f"\n=== {title} ===")
        try:
            rc = subprocess.call(argv, cwd=str(root))
        except OSError as exc:
            print(f"[HATA] {agent} baslatilamadi: {exc}")
            failed.append((agent, 1))
            continue
        if rc != 0:
            print(f"[BASARISIZ] {agent} rc={rc}")
            failed.append((agent, rc))
        else:
            print(f"[TAMAM] {agent}")

    print("\n=== Ozet ===")
    ok_n = len(old) - len(failed)
    print(f"Denendi: {len(old)}, basarili: {ok_n}, basarisiz: {len(failed)}")
    for name, rc in failed:
        print(f"  {name}: rc={rc}")
    return 0 if not failed else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())

"""Depoya ait artık süreçleri bulur ve kapatır (yalnız stdlib).

Neden var: ACP sağlık testi ajanı başlatıp el sıkışma bitince süreci öldürür,
ama bazı ajanlar (ölçüldü: `cline`, `goose`) asıl işi bir ALT sürece yaptırır ve
o alt süreç öksüz kalır. Birikince iki somut zarar veriyor:

* `npm install` **EBUSY** ile düşüyor — çalışan `.exe` kilitli (2026-07-27,
  OpenCode güncellemesi).
* Klasör taşınamıyor — "Permission denied" (2026-07-27, eski ağacın arşivlenmesi).

Kapsam dar tutulur: yalnız **bu depo içindeki** ACP ajan ikilileri sayılır.
Sistemdeki başka bir ajan kurulumuna, kullanıcının elle açtığı bir CLI'ya veya
yerel model sunucusuna dokunulmaz.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from tools.setup_gui.detect import IS_WIN, agent_specs

# Yerel model sunucusu kasten DIŞARIDA: uzun ömürlü olması normaldir ve
# kullanıcının başka işleri ona bağlı olabilir.
_PS_LIST = (
    "Get-CimInstance Win32_Process | "
    "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath | ConvertTo-Json -Compress"
)


def _all_processes() -> list[dict]:
    """(pid, ad, yol) üçlüleri. Windows dışında veya hata durumunda boş liste."""
    if not IS_WIN:
        return []
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_LIST],
            capture_output=True,
            text=True,
            timeout=45,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0 or not (out.stdout or "").strip():
        return []
    try:
        doc = json.loads(out.stdout)
    except json.JSONDecodeError:
        return []
    rows = doc if isinstance(doc, list) else [doc]
    return [r for r in rows if isinstance(r, dict)]


def juggler_running(root: Path) -> bool:
    """Panel açık mı? Açıksa ajan süreçleri meşru sayılır — dokunulmaz."""
    for p in _all_processes():
        if str(p.get("Name") or "").lower() in {"juggler.exe", "juggler-app.exe"}:
            return True
    return False


def agent_binaries(root: Path) -> set[str]:
    """Depo içindeki ACP ajan ikililerinin küçük harfe indirgenmiş yolları."""
    out: set[str] = set()
    for spec in agent_specs(root).values():
        try:
            out.add(str(Path(spec["bin"]).resolve()).lower())
        except (OSError, ValueError):
            continue
    return out


def agent_names(root: Path) -> set[str]:
    """Ajan ikililerinin uzantısız adları (küçük harf).

    Yol eşleşmesi tek başına YETMİYOR: npm ajanları asıl işi ayrı bir platform
    paketinde yapar — cline'ın kaydı `node_modules/cline/bin/cline` iken çalışan
    süreç `node_modules/@cline/cli-windows-x64/bin/cline.exe`. İkincisi birincinin
    kardeşi değil, o yüzden yalnız yola bakan ölçüt onu kaçırıyordu (ölçüldü:
    2026-07-27, `npm install` EBUSY'sine yol açan süreç tam olarak buydu).
    Ada göre eşleşme bunu yakalar; kapsam yine depo içiyle sınırlıdır.
    """
    return {Path(b).stem.lower() for b in agent_binaries(root)}


def stray(root: Path) -> list[dict]:
    """Depoya ait, ARTIK olduğu düşünülen ajan süreçleri.

    Ölçüt: çalıştırılabilir dosya bu deponun içinde VE bir ACP ajanına ait.
    Panel açıkken boş liste döner (o süreçler o an kullanılıyor olabilir).
    """
    if juggler_running(root):
        return []
    root_s = str(root.resolve()).lower()
    bins = agent_binaries(root)
    names = agent_names(root)
    me = os.getpid()
    found: list[dict] = []
    for p in _all_processes():
        path = str(p.get("ExecutablePath") or "")
        if not path:
            continue
        low = path.lower()
        if not low.startswith(root_s):
            continue  # depo dışı — bizim işimiz değil
        # Kayıtlı ikilinin kendisi, yanındaki yardımcı, ya da AYNI ADI taşıyan
        # bir ikili (npm platform paketleri: @cline/cli-windows-x64/bin/cline.exe).
        if not (
            low in bins
            or Path(low).stem in names
            or any(low.startswith(str(Path(b).parent).lower()) for b in bins)
        ):
            continue
        pid = int(p.get("ProcessId") or 0)
        if pid in (0, me):
            continue
        found.append({"pid": pid, "name": str(p.get("Name") or ""), "path": path})
    return found


def kill(pids: list[int]) -> dict:
    """Verilen PID'leri kapatır. Dönüş: {killed, gone, failed}.

    `gone` = kapatma anında zaten yoktu. Bu normaldir ve BAŞARISIZLIK DEĞİLDİR:
    bir üst süreci kapatmak alt süreçlerini de götürür, listedeki sonraki PID'ler
    çoktan ölmüş olur. Ayrı sayılmazsa temizlik hep "kısmen başarısız" görünür.
    """
    killed, gone, failed = [], [], []
    for pid in pids:
        try:
            r = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)] if IS_WIN else ["kill", "-9", str(pid)],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            failed.append(f"{pid}: {exc}")
            continue
        blob = ((r.stdout or "") + (r.stderr or "")).lower()
        if r.returncode == 0:
            killed.append(pid)
        elif "not found" in blob or "no such process" in blob:
            gone.append(pid)
        else:
            failed.append(f"{pid}: {blob.strip()[:80]}")
    return {"killed": killed, "gone": gone, "failed": failed}

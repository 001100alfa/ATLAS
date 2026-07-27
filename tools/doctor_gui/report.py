"""Tarama sonucundan insan-okur Markdown rapor üretir.

Rapor arayüzdekiyle AYNI üç bilgiyi taşır — kanıt, kaynak, çözüm — çünkü asıl
işi ekranı kapattıktan sonra da elde kalmaktır: bir arıza kaydına eklenebilir,
başkasına gönderilebilir, iki tarama arasında karşılaştırılabilir.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import checks, versions

ICON = {"ok": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}


def reports_dir(root: Path) -> Path:
    return root / ".atlas" / "doctor" / "reports"


def render(root: Path, steps: dict[str, list[dict]], stamp: str) -> str:
    all_findings = [f for step in checks.STEPS for f in steps.get(step["id"], [])]
    summary = checks.summarize(all_findings)
    c = summary["counts"]

    lines = [
        "# ATLAS — Sağlık & Güncelleme Raporu",
        "",
        f"- **Tarih:** {stamp}",
        f"- **Proje:** `{root}`",
        f"- **Sonuç:** {c['ok']} sağlam · {c['warn']} uyarı · {c['fail']} engel",
        "",
    ]

    if summary["blocking"]:
        lines += [
            "> **Engelleyen sorun var.** Aşağıdaki ❌ maddeleri giderilmeden panel/ajan "
            "bağlantısı güvenilir çalışmaz.",
            "",
        ]

    lines += ["## Kurulu sürümler", "", "| Bileşen | Yerel | Üstakım |", "|---|---|---|"]
    local = versions.local_versions(root)
    for comp in sorted(local):
        latest = versions._REMOTE_CACHE.get(comp)
        lines.append(f"| {comp} | {local[comp] or '—'} | {latest or '—'} |")
    lines.append("")

    for step in checks.STEPS:
        found = steps.get(step["id"])
        if not found:
            continue
        lines += [f"## {step['label']}", ""]
        for f in found:
            lines.append(f"### {ICON.get(f['status'], '•')} {f['title']}")
            lines.append("")
            lines.append(f"- **Ölçülen:** {f['detail']}")
            if f.get("cause"):
                lines.append(f"- **Kaynağı:** {f['cause']}")
            if f.get("remedy"):
                lines.append(f"- **Çözüm:** {f['remedy']}")
            for ev in f.get("evidence") or []:
                lines += ["", "```", ev.strip(), "```"]
            lines.append("")

    lines += [
        "---",
        "",
        "Bu rapor `DOCTOR.cmd` tarafından üretildi. Denetimlerin ne yaptığı: `docs/DOCTOR-GUI.md`.",
        "",
    ]
    return "\n".join(lines)


def write_report(root: Path, steps: dict[str, list[dict]]) -> Path:
    now = datetime.now()
    d = reports_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"saglik-{now:%Y%m%d-%H%M%S}.md"
    path.write_text(render(root, steps, f"{now:%d.%m.%Y %H:%M}"), encoding="utf-8")
    return path

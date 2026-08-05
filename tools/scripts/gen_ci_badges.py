"""SPEC 082: `.github/workflows/*.yml` içindeki workflow'ları README'de
badge tablosuna dönüştür.

Statik script — kullanıcı manuel çalıştırır veya CI drift gate.

Kullanım:
    python tools/scripts/gen_ci_badges.py [--repo OWNER/REPO]
    python tools/scripts/gen_ci_badges.py --check   # drift kontrol (exit 1)

README.md içinde `<!-- ci-status:start -->` ve `<!-- ci-status:end -->`
markörleri arasına yerleştirir. Marker yoksa README sonuna eklenir.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOWS_DIR = _REPO_ROOT / ".github" / "workflows"
_README = _REPO_ROOT / "README.md"
_START_MARKER = "<!-- ci-status:start -->"
_END_MARKER = "<!-- ci-status:end -->"

# Default fallback (GitHub Actions env'de override edilir)
_DEFAULT_REPO_SLUG = "001100alfa/ATLAS"


def _detect_repo_slug() -> str:
    """GitHub Actions env `GITHUB_REPOSITORY` (OWNER/REPO). Yoksa default."""
    env = os.environ.get("GITHUB_REPOSITORY", "").strip()
    return env if env else _DEFAULT_REPO_SLUG


def _extract_workflow_name(yaml_path: Path) -> str:
    """YAML'dan `name:` satırını basit regex ile çıkar (PyYAML gerektirmez)."""
    text = yaml_path.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*(.+?)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    return yaml_path.stem  # fallback


def _collect_workflows() -> list[tuple[str, str]]:
    """`(workflow_name, file_name)` alfabetik sıralı."""
    if not _WORKFLOWS_DIR.is_dir():
        return []
    out = []
    for p in sorted(_WORKFLOWS_DIR.glob("*.yml")):
        out.append((_extract_workflow_name(p), p.name))
    return out


def _build_badge_block(repo_slug: str) -> str:
    """Markdown badge tablosu — deterministik sıra."""
    workflows = _collect_workflows()
    lines = [
        _START_MARKER,
        "",
        "## CI Durumu",
        "",
        "| Workflow | Durum |",
        "|---|---|",
    ]
    for wf_name, file_name in workflows:
        badge_url = (
            f"https://github.com/{repo_slug}/actions/workflows/"
            f"{file_name}/badge.svg"
        )
        actions_url = (
            f"https://github.com/{repo_slug}/actions/workflows/{file_name}"
        )
        lines.append(f"| {wf_name} | [![{wf_name}]({badge_url})]({actions_url}) |")
    lines.append("")
    lines.append(_END_MARKER)
    return "\n".join(lines)


def _update_readme(block: str) -> tuple[bool, str]:
    """README'yi güncelle. Return: `(değişti_mi, yeni_içerik)`."""
    original = _README.read_text(encoding="utf-8") if _README.is_file() else ""
    if _START_MARKER in original and _END_MARKER in original:
        # Marker'lar arası bloğu değiştir
        pattern = re.compile(
            re.escape(_START_MARKER) + r".*?" + re.escape(_END_MARKER),
            re.DOTALL,
        )
        updated = pattern.sub(block, original)
    else:
        # Marker yok — README sonuna ekle
        sep = "" if original.endswith("\n\n") else ("\n" if original.endswith("\n") else "\n\n")
        updated = original + sep + block + "\n"
    return updated != original, updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SPEC 082: README CI badge tablosu üret/doğrula."
    )
    parser.add_argument(
        "--repo", default=None,
        help="OWNER/REPO slug (GITHUB_REPOSITORY env override, "
             f"default '{_DEFAULT_REPO_SLUG}')",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Sadece drift kontrol — README güncel değilse exit 1.",
    )
    args = parser.parse_args(argv)
    repo_slug = args.repo or _detect_repo_slug()
    block = _build_badge_block(repo_slug)
    changed, updated = _update_readme(block)
    if args.check:
        if changed:
            # ASCII-only (SPEC 057 [KALIP]: Windows cp1254 stdout uyumu)
            print(
                "README ci-status blogu guncel degil. "
                "Calistir: python tools/scripts/gen_ci_badges.py",
                file=sys.stderr,
            )
            return 1
        print("OK: README ci-status guncel.")
        return 0
    if changed:
        _README.write_text(updated, encoding="utf-8")
        print(f"README guncellendi: {_README}")
    else:
        print("README zaten guncel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

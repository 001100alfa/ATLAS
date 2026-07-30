"""SPEC 037 — atlas ai-cli diff-summary testleri."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import (
    _format_bumps,
    _parse_package_lock_diff,
    main,
)

# ─────────────────────────────────────────────────────────────────────
# _parse_package_lock_diff — düz metin parse (subprocess yok)
# ─────────────────────────────────────────────────────────────────────


def test_037_parse_bos_diff() -> None:
    """Boş diff → boş liste."""
    assert _parse_package_lock_diff("") == []


def test_037_parse_tek_paket_bump() -> None:
    """Tek paket bump — (paket, eski, yeni)."""
    diff = """diff --git a/tools/ai-cli/package-lock.json b/tools/ai-cli/package-lock.json
--- a/tools/ai-cli/package-lock.json
+++ b/tools/ai-cli/package-lock.json
@@ -100,7 +100,7 @@
     "node_modules/opencode-ai": {
-      "version": "1.18.8",
+      "version": "1.18.9",
       "resolved": "..."
"""
    bumps = _parse_package_lock_diff(diff)
    assert len(bumps) == 1
    pkg, old, new = bumps[0]
    assert "opencode-ai" in pkg
    assert old == "1.18.8"
    assert new == "1.18.9"


def test_037_parse_coklu_paket_bump() -> None:
    """İki paket bump."""
    diff = """--- a/tools/ai-cli/package-lock.json
+++ b/tools/ai-cli/package-lock.json
     "node_modules/opencode-ai": {
-      "version": "1.18.8",
+      "version": "1.18.9",
     "node_modules/cline": {
-      "version": "3.0.46",
+      "version": "3.0.47",
"""
    bumps = _parse_package_lock_diff(diff)
    assert len(bumps) == 2
    pkgs = {b[0] for b in bumps}
    assert any("opencode-ai" in p for p in pkgs)
    assert any("cline" in p for p in pkgs)


# ─────────────────────────────────────────────────────────────────────
# _format_bumps — commit msg biçimi
# ─────────────────────────────────────────────────────────────────────


def test_037_format_bos() -> None:
    assert _format_bumps([]) == "(diff yok)"


def test_037_format_tek_paket() -> None:
    out = _format_bumps([("opencode-ai", "1.18.8", "1.18.9")])
    assert out == "chore(ai-cli): opencode-ai 1.18.8 → 1.18.9"


def test_037_format_coklu_paket() -> None:
    out = _format_bumps([
        ("opencode-ai", "1.18.8", "1.18.9"),
        ("cline", "3.0.46", "3.0.47"),
    ])
    assert "chore(ai-cli):" in out
    assert "opencode-ai 1.18.8 → 1.18.9" in out
    assert "cline 3.0.46 → 3.0.47" in out
    assert "; " in out


# ─────────────────────────────────────────────────────────────────────
# _cmd_ai_cli_diff_summary — end-to-end (git subprocess mocked)
# ─────────────────────────────────────────────────────────────────────


def test_037_cmd_diff_yok(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Git diff çıktısı boş → `(diff yok)`."""
    monkeypatch.setattr(
        cli_mod, "_run_git_diff_package_lock", lambda: ("", None),
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "(diff yok)"


def test_037_cmd_tek_bump(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Mocked diff → tek bump commit mesajı."""
    fake_diff = (
        '     "node_modules/opencode-ai": {\n'
        '-      "version": "1.18.8",\n'
        '+      "version": "1.18.9",\n'
    )
    monkeypatch.setattr(
        cli_mod, "_run_git_diff_package_lock", lambda: (fake_diff, None),
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out == "chore(ai-cli): opencode-ai 1.18.8 → 1.18.9"


def test_037_cmd_git_yok_failsafe(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Git yoksa (`error` dolu) → fail-safe uyarı + exit 0."""
    monkeypatch.setattr(
        cli_mod, "_run_git_diff_package_lock",
        lambda: ("", "git çağrısı başarısız: FileNotFoundError"),
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("(diff okunamadı:")
    assert "git çağrısı başarısız" in out


def test_037_cmd_dosya_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """`_AI_CLI_PACKAGE_LOCK` yoksa fail-safe (gerçek fonksiyon çağrılır)."""
    monkeypatch.setattr(
        cli_mod, "_AI_CLI_PACKAGE_LOCK", tmp_path / "olmayan-lock.json",
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert "dosya yok" in out

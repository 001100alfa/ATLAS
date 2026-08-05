"""SPEC 094 — atlas ai-cli list --outdated --strict testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import main


def _make_ai_cli_layout(
    root: Path,
    deps: dict[str, str],
    installed: dict[str, str] | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps({"name": "atlas-ai-cli", "dependencies": deps}),
        encoding="utf-8",
    )
    if installed:
        for name, ver in installed.items():
            pd = root / "node_modules" / name
            pd.mkdir(parents=True, exist_ok=True)
            (pd / "package.json").write_text(
                json.dumps({"name": name, "version": ver}),
                encoding="utf-8",
            )


def test_094_outdated_strict_bos_exit_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Hepsi güncel + --outdated --strict → exit 0."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"opencode-ai": "^1.18.8", "cline": "~3.0.47"},
        installed={"opencode-ai": "1.18.8", "cline": "3.0.47"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--strict"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(guncelleme yok)" in out


def test_094_outdated_strict_bulgu_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Outdated var + --strict → exit 4 (CI kırar)."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^1.0.0", "b": "^2.0.0"},
        installed={"a": "1.0.0"},  # b kurulu değil → outdated
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--strict"])
    assert rc == 4
    cap = capsys.readouterr()
    assert "b" in cap.out  # bulgu satırı yine basılır
    assert "SAĞLIK BAŞARISIZ" in cap.err
    assert "--strict" in cap.err


def test_094_outdated_strict_json_bulgu_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json + --outdated --strict + bulgu → exit 4, JSON yazılır."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},  # outdated
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--strict", "--json"])
    assert rc == 4
    data = json.loads(capsys.readouterr().out.strip())
    assert len(data["packages"]) == 1
    assert data["packages"][0]["name"] == "a"


def test_094_strict_outdated_yoksa_mutex_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--strict tek başına (outdated yok) → SPEC HATASI exit 2."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--strict"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--strict" in err
    assert "--outdated" in err


def test_094_outdated_yalın_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--outdated (strict yok) + bulgu → exit 0 (SPEC 088 BİT-UYUMLU)."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated"])
    assert rc == 0


def test_094_yalin_list_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Yalın `ai-cli list` (strict/outdated yok) → SPEC 037.2 exit 0."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list"])
    assert rc == 0

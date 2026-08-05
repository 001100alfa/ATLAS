"""SPEC 099 — atlas ai-cli list --outdated --json-lines testleri."""

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


def test_099_jsonl_paket_basina_satir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """2 outdated paket → 2 satır + 1 summary satırı."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0", "b": "^3.0.0", "c": "^1.0.0"},
        installed={"a": "1.0.0", "c": "1.0.0"},  # a, b outdated; c güncel
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--json-lines"])
    assert rc == 0
    out = capsys.readouterr().out.strip().split("\n")
    parsed = [json.loads(ln) for ln in out]
    # 2 outdated + 1 summary
    assert len(parsed) == 3
    types = [p.get("type", "package") for p in parsed]
    assert types[-1] == "summary"
    summary = parsed[-1]
    assert summary["outdated"] == 2
    assert summary["total_deps"] == 3


def test_099_jsonl_clean_yalnız_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Hepsi güncel → yalnız 1 summary satırı, outdated=0."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^1.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--json-lines"])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 1
    summary = json.loads(lines[0])
    assert summary["type"] == "summary"
    assert summary["outdated"] == 0
    assert summary["total_deps"] == 1


def test_099_jsonl_paket_alanlari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Paket satırları SPEC 088 JSON alanlarıyla AYNI (name/expected/installed)."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"foo": "^2.0.0"},
        installed={"foo": "1.5.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--json-lines"])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    pkg = json.loads(lines[0])
    assert pkg["name"] == "foo"
    assert pkg["expected"] == "^2.0.0"
    assert pkg["installed"] == "1.5.0"


def test_099_jsonl_outdated_yoksa_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json-lines yalın (outdated yok) → SPEC HATASI exit 2."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--json-lines"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--json-lines" in err
    assert "--outdated" in err


def test_099_jsonl_json_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json-lines + --json → MUTEX exit 2."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines", "--json",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MUTEX" in err or "birlikte" in err


def test_099_jsonl_strict_ile_bulgu_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--outdated --json-lines --strict + bulgu → exit 4, NDJSON hâlâ basılır."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},  # outdated
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines", "--strict",
    ])
    assert rc == 4
    out = capsys.readouterr().out.strip().split("\n")
    assert len(out) == 2  # 1 paket + summary
    # Her satır valid JSON
    for ln in out:
        json.loads(ln)


def test_099_jsonl_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json-lines YOK → SPEC 088 --json davranışı AYNI."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "path" in data
    assert "packages" in data
    assert len(data["packages"]) == 1

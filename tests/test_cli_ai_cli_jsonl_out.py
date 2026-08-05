"""SPEC 106 — atlas ai-cli list --outdated --json-lines --out PATH testleri."""

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


def test_106_out_yazma_stdout_bos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out PATH → dosya, stdout NDJSON basmaz."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert not stdout.strip().startswith("{")


def test_106_out_icerik_stdout_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dosya içeriği stdout modu ile AYNI."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0", "b": "^3.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    # stdout
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
    ])
    assert rc == 0
    stdout_lines = capsys.readouterr().out.strip().split("\n")
    # --out
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(out),
    ])
    assert rc == 0
    file_lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert file_lines == stdout_lines


def test_106_out_parent_auto_mkdir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "deep" / "sub" / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()


def test_106_out_yazma_hatasi_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(target),
    ])
    assert rc == 2


def test_106_out_jsonl_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out --json-lines yok → SPEC HATASI exit 2."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--out", str(out),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err
    assert "--json-lines" in err


def test_106_out_strict_bulgu_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out + --strict + bulgu → exit 4, dosyaya yazılır."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(out), "--strict",
    ])
    assert rc == 4
    assert out.is_file()
    lines = out.read_text(encoding="utf-8").strip().split("\n")
    for ln in lines:
        json.loads(ln)


def test_106_out_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out YOK → SPEC 099 stdout AYNI."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^2.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    for ln in out.strip().split("\n"):
        json.loads(ln)

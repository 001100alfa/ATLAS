"""SPEC 109 — atlas ai-cli list --outdated --json-lines --out --gzip testleri."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import main


def _make_layout(root: Path, deps: dict[str, str],
                 installed: dict[str, str] | None = None) -> None:
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


def test_109_gzip_auto_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"a": "^2.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert not out.is_file()
    assert (tmp_path / "r.jsonl.gz").is_file()


def test_109_gzip_decompress_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"a": "^2.0.0", "b": "^3.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    plain = tmp_path / "p.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines", "--out", str(plain),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    gz = tmp_path / "g.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines", "--out", str(gz), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "g.jsonl.gz", "rt", encoding="utf-8") as fh:
        gz_text = fh.read()
    assert gz_text == plain_text


def test_109_gzip_out_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err
    assert "--out" in err


def test_109_gzip_magic_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert (tmp_path / "r.jsonl.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_109_gzip_strict_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--strict + bulgu + --gzip → exit 4, gzip'e yazılır."""
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"a": "^2.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines",
        "--out", str(out), "--gzip", "--strict",
    ])
    assert rc == 4
    assert (tmp_path / "r.jsonl.gz").is_file()


def test_109_gzip_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"a": "^1.0.0"}, installed={"a": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "r.jsonl"
    rc = main([
        "ai-cli", "list", "--outdated", "--json-lines", "--out", str(out),
    ])
    assert rc == 0
    assert out.read_bytes()[:2] != b"\x1f\x8b"

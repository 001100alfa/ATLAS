"""SPEC 120 — atlas ai-cli status <name> --json-lines --out --gzip testleri."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

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


def test_120_gzip_auto_suffix(monkeypatch, tmp_path):
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "s.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert not out.is_file()
    assert (tmp_path / "s.jsonl.gz").is_file()


def test_120_gzip_decompress_bit_uyumlu(monkeypatch, tmp_path):
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    plain = tmp_path / "p.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines", "--out", str(plain),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    gz = tmp_path / "g.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines", "--out", str(gz), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "g.jsonl.gz", "rt", encoding="utf-8") as fh:
        assert fh.read() == plain_text


def test_120_gzip_out_yok_mutex(monkeypatch, tmp_path, capsys):
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main([
        "ai-cli", "status", "foo", "--json-lines", "--gzip",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--gzip" in err and "--out" in err


def test_120_gzip_magic_bytes(monkeypatch, tmp_path):
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "s.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    assert (tmp_path / "s.jsonl.gz").read_bytes()[:2] == b"\x1f\x8b"


def test_120_gzip_ndjson_valid_lines(monkeypatch, tmp_path):
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "s.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines",
        "--out", str(out), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "s.jsonl.gz", "rt", encoding="utf-8") as fh:
        lines = fh.read().strip().split("\n")
    assert len(lines) == 9  # 8 field + summary
    for ln in lines:
        json.loads(ln)


def test_120_gzip_yoksa_duz(monkeypatch, tmp_path):
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "s.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines", "--out", str(out),
    ])
    assert rc == 0
    assert out.read_bytes()[:2] != b"\x1f\x8b"

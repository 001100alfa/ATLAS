"""SPEC 118 — atlas ai-cli status <name> --json-lines --out testleri."""

from __future__ import annotations

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


def test_118_status_jsonl_field_lines(monkeypatch, tmp_path, capsys):
    """--json-lines → 8 alan satırı + 1 summary."""
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "status", "foo", "--json-lines"])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 9  # 8 field + 1 summary
    parsed = [json.loads(ln) for ln in lines]
    assert parsed[-1]["type"] == "summary"
    assert parsed[-1]["name"] == "foo"
    assert parsed[-1]["up_to_date"] is True


def test_118_status_jsonl_out_file(monkeypatch, tmp_path, capsys):
    """--out PATH → dosya, stdout bos."""
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "s.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines", "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert stdout.strip() == ""
    lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 9


def test_118_status_json_jsonl_mutex(monkeypatch, tmp_path, capsys):
    """--json + --json-lines → exit 2."""
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main([
        "ai-cli", "status", "foo", "--json", "--json-lines",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MUTEX" in err or "birlikte" in err


def test_118_status_out_jsonl_yok_mutex(monkeypatch, tmp_path, capsys):
    """--out --json-lines yok → exit 2."""
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "s.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--out", str(out),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err
    assert "--json-lines" in err


def test_118_status_parent_auto_mkdir(monkeypatch, tmp_path):
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    out = tmp_path / "deep" / "sub" / "s.jsonl"
    rc = main([
        "ai-cli", "status", "foo", "--json-lines", "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()


def test_118_status_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--json-lines YOK → SPEC 037.4 --json AYNI."""
    ai = tmp_path / "ai-cli"
    _make_layout(ai, deps={"foo": "^1.0.0"}, installed={"foo": "1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "status", "foo", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["name"] == "foo"
    assert "installed_version" in data

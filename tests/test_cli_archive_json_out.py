"""SPEC 115 — atlas archive --list --json --out PATH testleri."""

from __future__ import annotations

import gzip
import json
import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _mktar(arc: Path, name: str) -> Path:
    arc.mkdir(parents=True, exist_ok=True)
    p = arc / name
    with tarfile.open(p, "w:gz") as tar:
        info = tarfile.TarInfo(name="x")
        info.size = 0
        tar.addfile(info)
    return p


def test_115_out_json_yazma(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    _mktar(arc, "b.tar.gz")
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 2


def test_115_out_json_stdout_bos(monkeypatch, tmp_path, capsys):
    """--out ile stdout JSON basmaz."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert capsys.readouterr().out.strip() == ""


def test_115_out_json_icerik_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """Dosya içeriği stdout --json ile AYNI."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    _mktar(arc, "b.tar.gz")
    rc = main([
        "archive", "--list", "--json",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    stdout_text = capsys.readouterr().out.strip()
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.read_text(encoding="utf-8") == stdout_text


def test_115_out_json_gzip(monkeypatch, tmp_path):
    """--json --out --gzip birlikte."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(out), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    gz = tmp_path / "r.json.gz"
    assert gz.is_file()
    with gzip.open(gz, "rt", encoding="utf-8") as fh:
        data = json.loads(fh.read())
    assert isinstance(data, list)


def test_115_out_json_yok_ve_jsonl_yok_mutex(monkeypatch, tmp_path, capsys):
    """--out yalın (json/jsonl yok) → exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--list", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err
    assert "--json" in err


def test_115_out_json_parent_auto_mkdir(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz")
    out = tmp_path / "deep" / "sub" / "r.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.is_file()


def test_115_out_json_sort_limit_ortogonal(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "small.tar.gz")
    _mktar(arc, "big.tar.gz")
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(out),
        "--sort-by", "name", "--limit", "1",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["archive"] == "big.tar.gz"

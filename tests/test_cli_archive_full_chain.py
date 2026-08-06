"""SPEC 121 — atlas archive tam zincir regresyon.

SPEC 075 (--list) + 079 (--sort-by) + 085 (--limit) + 093 (--name-match)
+ 108 (--gzip) + 115 (--json --out) birlikte kullanıldığında beklenen
sonuç. Kod değişikliği yok; regresyon önleme kanıtı.
"""

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


def _mktar(arc: Path, name: str, members: list[str]) -> None:
    arc.mkdir(parents=True, exist_ok=True)
    with tarfile.open(arc / name, "w:gz") as tar:
        for m in members:
            info = tarfile.TarInfo(name=m)
            info.size = 0
            tar.addfile(info)


def test_121_tam_zincir_json_out_gzip(monkeypatch, tmp_path):
    """--json + --out + --gzip: tek JSON dizisi gzip dosyada."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    _mktar(arc, "b.tar.gz", ["x"])
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
    assert len(data) == 2


def test_121_tam_zincir_jsonl_out_gzip(monkeypatch, tmp_path):
    """--json-lines + --out + --gzip: NDJSON gzip'te + summary satır."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    _mktar(arc, "b.tar.gz", ["x"])
    _mktar(arc, "c.tar.gz", ["x"])
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    with gzip.open(tmp_path / "r.jsonl.gz", "rt", encoding="utf-8") as fh:
        lines = fh.read().strip().split("\n")
    assert len(lines) == 4  # 3 arşiv + summary
    assert json.loads(lines[-1])["type"] == "summary"
    assert json.loads(lines[-1])["count"] == 3


def test_121_tam_zincir_filter_sort_limit_gzip(monkeypatch, tmp_path):
    """--name-match + --sort-by size --desc + --limit + gzip zinciri."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "backup-1.tar.gz", ["x"] * 1)
    _mktar(arc, "backup-2.tar.gz", ["x"] * 10)
    _mktar(arc, "backup-3.tar.gz", ["x"] * 100)
    _mktar(arc, "task-1.tar.gz", ["x"] * 1000)  # filtreden geçmez
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines",
        "--name-match", "^backup",
        "--sort-by", "size", "--desc", "--limit", "2",
        "--out", str(out), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    with gzip.open(tmp_path / "r.jsonl.gz", "rt", encoding="utf-8") as fh:
        lines = fh.read().strip().split("\n")
    # backup filtre + size desc + limit 2 → backup-3, backup-2 + summary
    entries = [json.loads(ln) for ln in lines[:-1]]
    assert [e["archive"] for e in entries] == ["backup-3.tar.gz", "backup-2.tar.gz"]


def test_121_json_out_gzip_decompress_bit_uyumlu(monkeypatch, tmp_path):
    """Gzip decompress → düz --json --out ile içerik AYNI."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    plain = tmp_path / "p.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(plain),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    plain_text = plain.read_text(encoding="utf-8")
    gz = tmp_path / "g.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(gz), "--gzip",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    with gzip.open(tmp_path / "g.json.gz", "rt", encoding="utf-8") as fh:
        assert fh.read() == plain_text

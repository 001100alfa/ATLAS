"""SPEC 129 — vault verify --format json-lines --out --gzip regresyon.

SPEC 087+092+111+042 zinciri birlikte. Kod değişikliği yok; regresyon
önleme (SPEC 121/122/123 kalıbı).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.memory.vault import Vault


def _make_vault(root: Path, notes: dict[str, str]) -> Vault:
    root.mkdir(parents=True, exist_ok=True)
    for name, content in notes.items():
        (root / f"{name}.md").write_text(content, encoding="utf-8")
    return Vault(root)


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def test_129_tam_zincir_jsonl_out_gzip(monkeypatch, tmp_path):
    """--format json-lines + --out + --gzip: dosya + gzip + NDJSON."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok1]] [[yok2]]", "orfan": "içerik"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    gz = tmp_path / "r.jsonl.gz"
    assert gz.is_file()
    with gzip.open(gz, "rt", encoding="utf-8") as fh:
        lines = fh.read().strip().split("\n")
    # 2 broken + orfan(lar) + summary; hepsi valid JSON
    for ln in lines:
        json.loads(ln)
    types = [json.loads(ln)["type"] for ln in lines]
    assert types.count("broken_link") == 2
    assert types[-1] == "summary"


def test_129_tam_zincir_strict_bulgu_exit_4(monkeypatch, tmp_path):
    """--strict + bulgu + gzip → exit 4, dosya yazılır."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip", "--strict",
    ])
    assert rc == 4
    assert (tmp_path / "r.jsonl.gz").is_file()


def test_129_tam_zincir_dump_report_ortogonal(monkeypatch, tmp_path):
    """--out (gzip NDJSON) ile --dump-report (markdown) ortogonal."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    out = tmp_path / "r.jsonl"
    md = tmp_path / "r.md"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip",
        "--dump-report", str(md),
    ])
    assert rc == 0
    assert (tmp_path / "r.jsonl.gz").is_file()
    assert md.is_file()
    assert "#" in md.read_text(encoding="utf-8")


def test_129_tam_zincir_temiz_vault(monkeypatch, tmp_path):
    """Temiz vault + gzip → yalnız summary (clean=True)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {
        "a": "[[b]] #ortak",
        "b": "[[a]] #ortak",
    })
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--gzip",
    ])
    assert rc == 0
    with gzip.open(tmp_path / "r.jsonl.gz", "rt", encoding="utf-8") as fh:
        lines = fh.read().strip().split("\n")
    assert len(lines) == 1
    summary = json.loads(lines[0])
    assert summary["type"] == "summary"
    assert summary["clean"] is True

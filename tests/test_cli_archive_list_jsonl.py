"""SPEC 098 — atlas archive --list --json-lines testleri."""

from __future__ import annotations

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


def _mktar(arc: Path, name: str, members: list[str]) -> Path:
    arc.mkdir(parents=True, exist_ok=True)
    tar_path = arc / name
    with tarfile.open(tar_path, "w:gz") as tar:
        for m in members:
            info = tarfile.TarInfo(name=m)
            info.size = 0
            tar.addfile(info)
    return tar_path


def test_098_jsonl_arsiv_basina_satir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """3 arşiv → 3 satır + 1 summary."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    for n in ("a.tar.gz", "b.tar.gz", "c.tar.gz"):
        _mktar(arc, n, ["x"])
    rc = main([
        "archive", "--list", "--json-lines",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 4
    parsed = [json.loads(ln) for ln in lines]
    assert parsed[-1]["type"] == "summary"
    assert parsed[-1]["count"] == 3


def test_098_jsonl_arsiv_alanlari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Arşiv satırı SPEC 075 alanlarını içerir."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "task-001.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json-lines",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    first = json.loads(capsys.readouterr().out.strip().split("\n")[0])
    for f in ("archive", "task_id", "date", "size_bytes",
              "size_human", "member_count", "mtime"):
        assert f in first


def test_098_jsonl_bos_yalnız_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Boş dizin → yalnız 1 summary satırı (count=0)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    arc.mkdir()
    rc = main([
        "archive", "--list", "--json-lines",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 1
    summary = json.loads(lines[0])
    assert summary["type"] == "summary"
    assert summary["count"] == 0


def test_098_jsonl_json_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json + --json-lines → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json", "--json-lines",
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MUTEX" in err or "birlikte" in err


def test_098_jsonl_sort_limit_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--sort-by size --desc --limit 2 → NDJSON'da en büyük 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "small.tar.gz", ["x"] * 1)
    _mktar(arc, "medium.tar.gz", ["x"] * 10)
    _mktar(arc, "big.tar.gz", ["x"] * 100)
    _mktar(arc, "huge.tar.gz", ["x"] * 1000)
    rc = main([
        "archive", "--list", "--json-lines",
        "--sort-by", "size", "--desc", "--limit", "2",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    # 2 arşiv + 1 summary
    assert len(lines) == 3
    parsed = [json.loads(ln) for ln in lines]
    assert parsed[0]["archive"] == "huge.tar.gz"
    assert parsed[1]["archive"] == "big.tar.gz"
    assert parsed[2]["count"] == 2


def test_098_jsonl_name_match_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--name-match filtresi NDJSON öncesi uygulanır."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "backup-2026.tar.gz", ["x"])
    _mktar(arc, "task-001.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json-lines",
        "--name-match", "^backup",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    # 1 arşiv + 1 summary
    assert len(lines) == 2
    assert json.loads(lines[0])["archive"] == "backup-2026.tar.gz"
    assert json.loads(lines[1])["count"] == 1


def test_098_jsonl_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--json-lines YOK → SPEC 075 --json AYNI (tek dizi)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    _mktar(arc, "b.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 2

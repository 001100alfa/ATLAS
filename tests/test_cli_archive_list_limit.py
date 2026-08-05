"""SPEC 085 — atlas archive --list --limit N testleri."""

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


def test_085_limit_top_n_after_sort(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--sort-by size --desc --limit 2 → en büyük 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"] * 1)
    _mktar(arc, "b.tar.gz", ["x"] * 5)
    _mktar(arc, "c.tar.gz", ["x"] * 20)
    _mktar(arc, "d.tar.gz", ["x"] * 40)
    rc = main([
        "archive", "--list", "--json",
        "--sort-by", "size", "--desc", "--limit", "2",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 2
    # size desc: en büyük 2
    assert [e["archive"] for e in data] == ["d.tar.gz", "c.tar.gz"]


def test_085_limit_default_name_alpha(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--limit 2 tek başına: default name alfabetik ilk 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "zzz.tar.gz", ["x"])
    _mktar(arc, "aaa.tar.gz", ["x"])
    _mktar(arc, "mmm.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json", "--limit", "2",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert [e["archive"] for e in data] == ["aaa.tar.gz", "mmm.tar.gz"]


def test_085_limit_gt_len_returns_all(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--limit N > len(entries) → tüm liste (kesme yok, hata yok)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    _mktar(arc, "b.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json", "--limit", "99",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 2


def test_085_limit_zero_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--limit 0 → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--limit", "0",
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--limit" in err


def test_085_limit_negative_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--limit -5 → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--limit", "-5",
        "--archive-root", str(arc),
    ])
    assert rc == 2


def test_085_no_limit_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--limit VERİLMEZSE tam liste (SPEC 075/079 bit-uyumlu)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    for name in ("a.tar.gz", "b.tar.gz", "c.tar.gz", "d.tar.gz"):
        _mktar(arc, name, ["x"])
    rc = main([
        "archive", "--list", "--json",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 4


def test_085_limit_pretty_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pretty (non-JSON) çıktı da --limit uyar."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    for name in ("aaa.tar.gz", "bbb.tar.gz", "ccc.tar.gz"):
        _mktar(arc, name, ["x"])
    rc = main([
        "archive", "--list", "--limit", "1",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # aaa görünmeli, bbb/ccc görünmemeli (default name asc + limit 1)
    assert "aaa" in out
    assert "bbb" not in out
    assert "ccc" not in out


def test_085_limit_1_single_entry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--limit 1 → tek eleman."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"] * 3)
    _mktar(arc, "b.tar.gz", ["x"] * 1)
    rc = main([
        "archive", "--list", "--json",
        "--sort-by", "members", "--desc", "--limit", "1",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 1
    assert data[0]["archive"] == "a.tar.gz"

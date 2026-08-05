"""SPEC 079 — atlas archive --list --sort-by testleri."""

from __future__ import annotations

import json
import os
import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _mktar(arc: Path, name: str, members: list[str], mtime: float | None = None) -> Path:
    arc.mkdir(parents=True, exist_ok=True)
    tar_path = arc / name
    with tarfile.open(tar_path, "w:gz") as tar:
        for m in members:
            info = tarfile.TarInfo(name=m)
            info.size = 0
            tar.addfile(info)
    if mtime is not None:
        os.utime(tar_path, (mtime, mtime))
    return tar_path


def test_079_sort_by_default_name_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--sort-by yoksa (default `name`) SPEC 075 alfabetik bit-uyumlu."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "zzz-2026-01-01.tar.gz", ["a"])
    _mktar(arc, "aaa-2026-01-01.tar.gz", ["a"])
    _mktar(arc, "mmm-2026-01-01.tar.gz", ["a"])
    rc = main([
        "archive", "--list", "--json",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    names = [e["archive"] for e in data]
    assert names == ["aaa-2026-01-01.tar.gz", "mmm-2026-01-01.tar.gz",
                     "zzz-2026-01-01.tar.gz"]


def test_079_sort_by_size(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--sort-by size → küçükten büyüğe."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    # 3 arşiv farklı member sayısı → farklı size
    _mktar(arc, "a.tar.gz", ["x"] * 1)         # küçük
    _mktar(arc, "b.tar.gz", ["x"] * 5)         # orta
    _mktar(arc, "c.tar.gz", ["x"] * 20)        # büyük
    rc = main([
        "archive", "--list", "--json",
        "--sort-by", "size",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    sizes = [e["size_bytes"] for e in data]
    assert sizes == sorted(sizes)


def test_079_sort_by_size_desc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"] * 1)
    _mktar(arc, "b.tar.gz", ["x"] * 20)
    _mktar(arc, "c.tar.gz", ["x"] * 5)
    rc = main([
        "archive", "--list", "--json",
        "--sort-by", "size", "--desc",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    sizes = [e["size_bytes"] for e in data]
    assert sizes == sorted(sizes, reverse=True)


def test_079_sort_by_date(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--sort-by date → task_id-YYYY-MM-DD'deki date alanına göre."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "z-2026-03-15.tar.gz", ["a"])
    _mktar(arc, "a-2026-01-01.tar.gz", ["a"])
    _mktar(arc, "m-2026-02-10.tar.gz", ["a"])
    rc = main([
        "archive", "--list", "--json",
        "--sort-by", "date",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    dates = [e["date"] for e in data]
    assert dates == ["2026-01-01", "2026-02-10", "2026-03-15"]


def test_079_sort_by_members(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["m1"])                    # 1
    _mktar(arc, "b.tar.gz", ["m1", "m2", "m3"])        # 3
    _mktar(arc, "c.tar.gz", ["m1", "m2"])              # 2
    rc = main([
        "archive", "--list", "--json",
        "--sort-by", "members",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    counts = [e["member_count"] for e in data]
    assert counts == [1, 2, 3]


def test_079_sort_by_gecersiz_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--sort-by 'foo' → argparse choices reddi (exit 2 argparse)."""
    _env(monkeypatch, tmp_path)
    (tmp_path / "arc").mkdir()
    with pytest.raises(SystemExit) as excinfo:
        main([
            "archive", "--list", "--sort-by", "foo",
            "--archive-root", str(tmp_path / "arc"),
        ])
    assert excinfo.value.code == 2


def test_079_desc_bayragi_yalniz_ters_sira(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--desc name ile: z → a sırasına döner."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "aaa.tar.gz", ["x"])
    _mktar(arc, "zzz.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json", "--desc",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    names = [e["archive"] for e in data]
    assert names == ["zzz.tar.gz", "aaa.tar.gz"]


def test_079_insan_ciktisi_da_sirali(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "aaa.tar.gz", ["x"] * 1)
    _mktar(arc, "bbb.tar.gz", ["x"] * 10)
    rc = main([
        "archive", "--list", "--sort-by", "size", "--desc",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # bbb (büyük) önce, aaa sonra
    bbb_pos = out.find("bbb")
    aaa_pos = out.find("aaa")
    assert bbb_pos < aaa_pos

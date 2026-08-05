"""SPEC 093 — atlas archive --list --name-match PATTERN testleri."""

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


def test_093_name_match_prefix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--name-match '^backup' → sadece backup-* arşivler."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    for n in ("backup-2026-01.tar.gz", "backup-2026-02.tar.gz",
              "task-001.tar.gz", "test-xx.tar.gz"):
        _mktar(arc, n, ["x"])
    rc = main([
        "archive", "--list", "--json", "--name-match", "^backup",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    names = [e["archive"] for e in data]
    assert names == ["backup-2026-01.tar.gz", "backup-2026-02.tar.gz"]


def test_093_name_match_gecersiz_regex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Geçersiz regex → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--name-match", "[unclosed",
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--name-match" in err


def test_093_name_match_bos_sonuc_pretty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Filter boş sonuç → pretty '(esleme yok)' (bit-uyumluluk için ayrım)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--name-match", "hicbirisi",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(esleme yok)" in out
    assert "0 arsiv" in out


def test_093_name_match_arsiv_yok_pretty_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--name-match VERİLMEZ + boş dizin → SPEC 075 '(arsiv yok)' AYNI."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    arc.mkdir()
    rc = main([
        "archive", "--list",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert "(arsiv yok)" in capsys.readouterr().out


def test_093_name_match_sort_before(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--name-match sort ÖNCE uygulanır → sort filter'lı liste üzerinde."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "task-aaa.tar.gz", ["x"] * 1)
    _mktar(arc, "task-bbb.tar.gz", ["x"] * 10)
    _mktar(arc, "backup-xx.tar.gz", ["x"] * 100)
    rc = main([
        "archive", "--list", "--json",
        "--name-match", "^task",
        "--sort-by", "size", "--desc",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    names = [e["archive"] for e in data]
    # backup-xx filtreden geçmedi; task-bbb büyük, task-aaa küçük
    assert names == ["task-bbb.tar.gz", "task-aaa.tar.gz"]


def test_093_name_match_limit_kombinasyon(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--name-match + --sort-by + --limit tam zincir."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "backup-1.tar.gz", ["x"] * 1)
    _mktar(arc, "backup-2.tar.gz", ["x"] * 10)
    _mktar(arc, "backup-3.tar.gz", ["x"] * 100)
    _mktar(arc, "backup-4.tar.gz", ["x"] * 1000)
    _mktar(arc, "task-9.tar.gz", ["x"] * 10000)  # filtreden geçmez
    rc = main([
        "archive", "--list", "--json",
        "--name-match", "^backup",
        "--sort-by", "size", "--desc", "--limit", "2",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    names = [e["archive"] for e in data]
    # Filter → backup-1..4; sort size desc → 4,3,2,1; limit 2 → 4,3
    assert names == ["backup-4.tar.gz", "backup-3.tar.gz"]


def test_093_name_match_regex_orta(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Regex substring (`\\d{4}` gibi)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "task-2026-01.tar.gz", ["x"])
    _mktar(arc, "test-abc.tar.gz", ["x"])
    _mktar(arc, "backup-2025-12.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json",
        "--name-match", r"\d{4}-\d{2}",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    names = [e["archive"] for e in data]
    assert set(names) == {"task-2026-01.tar.gz", "backup-2025-12.tar.gz"}


def test_093_no_name_match_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--name-match VERİLMEZSE SPEC 075/079/085 BİT-UYUMLU."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    for n in ("zzz.tar.gz", "aaa.tar.gz", "mmm.tar.gz"):
        _mktar(arc, n, ["x"])
    rc = main([
        "archive", "--list", "--json",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    # Default name alfabetik AYNI
    assert [e["archive"] for e in data] == [
        "aaa.tar.gz", "mmm.tar.gz", "zzz.tar.gz",
    ]

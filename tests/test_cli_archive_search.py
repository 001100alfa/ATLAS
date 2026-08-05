"""SPEC 065 — atlas archive --search PATTERN testleri."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from atlas_core.cli import _search_archive_contents, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)


def _mktar(archive_root: Path, name: str, files: list[str]) -> Path:
    """Sahte tar.gz — verilen dosya adlarıyla."""
    archive_root.mkdir(parents=True, exist_ok=True)
    tar_path = archive_root / name
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in files:
            info = tarfile.TarInfo(name=f)
            info.size = 0
            tar.addfile(info)
    return tar_path


# ═════════════════════════════════════════════════════════════════════
# _search_archive_contents (birim)
# ═════════════════════════════════════════════════════════════════════


def test_065_search_archive_yok_bos_liste(tmp_path: Path) -> None:
    assert _search_archive_contents(tmp_path / "yok", "x") == []


def test_065_search_bulgu_yoksa_bos(tmp_path: Path) -> None:
    _mktar(tmp_path / "arc", "task-001-2026-01-01.tar.gz",
           ["task-001/a.md", "task-001/09-ship.md"])
    hits = _search_archive_contents(tmp_path / "arc", "xxxxx")
    assert hits == []


def test_065_search_tek_arsiv_esleme(tmp_path: Path) -> None:
    _mktar(tmp_path / "arc", "task-042-2026-07-31.tar.gz",
           ["task-042/00-need.md", "task-042/09-ship.md", "task-042/src/x.py"])
    hits = _search_archive_contents(tmp_path / "arc", r"\.md$")
    assert len(hits) == 1
    assert hits[0]["archive"] == "task-042-2026-07-31.tar.gz"
    assert set(hits[0]["matches"]) == {
        "task-042/00-need.md", "task-042/09-ship.md",
    }


def test_065_search_coklu_arsiv_deterministik_sira(tmp_path: Path) -> None:
    _mktar(tmp_path / "arc", "zzz-2026-01-01.tar.gz", ["zzz/x.md"])
    _mktar(tmp_path / "arc", "aaa-2026-01-01.tar.gz", ["aaa/x.md"])
    _mktar(tmp_path / "arc", "mmm-2026-01-01.tar.gz", ["mmm/x.md"])
    hits = _search_archive_contents(tmp_path / "arc", r"\.md")
    names = [h["archive"] for h in hits]
    assert names == sorted(names)  # alfabetik


def test_065_search_regex_gecersiz_valueerror(tmp_path: Path) -> None:
    (tmp_path / "arc").mkdir()
    with pytest.raises(ValueError, match="regex hatası"):
        _search_archive_contents(tmp_path / "arc", "[invalid")


def test_065_search_bozuk_tar_atlar(tmp_path: Path) -> None:
    """Bozuk .tar.gz → skipped, diğerleri işlenir."""
    _mktar(tmp_path / "arc", "iyi.tar.gz", ["iyi/x.md"])
    bad = tmp_path / "arc" / "bozuk.tar.gz"
    bad.write_bytes(b"not a real tar")
    hits = _search_archive_contents(tmp_path / "arc", r"\.md")
    assert len(hits) == 1
    assert hits[0]["archive"] == "iyi.tar.gz"


def test_065_search_case_insensitive_flag(tmp_path: Path) -> None:
    """Kullanıcı `(?i)` inline flag ile büyük/küçük harf duyarsız arama."""
    _mktar(tmp_path / "arc", "t.tar.gz",
           ["t/README.md", "t/notes/index.MD"])
    # Default duyarlı → sadece .md eşleşir
    hits_sensitive = _search_archive_contents(tmp_path / "arc", r"\.md$")
    assert len(hits_sensitive[0]["matches"]) == 1
    # (?i) → hem .md hem .MD eşleşir
    hits_insensitive = _search_archive_contents(tmp_path / "arc", r"(?i)\.md$")
    assert len(hits_insensitive[0]["matches"]) == 2


# ═════════════════════════════════════════════════════════════════════
# CLI: atlas archive --search
# ═════════════════════════════════════════════════════════════════════


def test_065_cli_search_arsiv_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main([
        "archive", "--search", "x",
        "--archive-root", str(tmp_path / "yok"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_065_cli_search_regex_gecersiz_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    (tmp_path / "arc").mkdir()
    rc = main([
        "archive", "--search", "[bad(",
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "regex hatası" in err


def test_065_cli_search_insan_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    _mktar(tmp_path / "arc", "task-042.tar.gz",
           ["task-042/00-need.md", "task-042/09-ship.md"])
    rc = main([
        "archive", "--search", r"\.md$",
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 arsivde 2 eslesme" in out
    assert "task-042.tar.gz" in out
    assert "task-042/00-need.md" in out


def test_065_cli_search_bulgu_yoksa_mesaj(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    _mktar(tmp_path / "arc", "t.tar.gz", ["t/x.py"])
    rc = main([
        "archive", "--search", r"\.md$",
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(bulgu yok)" in out


def test_065_cli_search_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    _mktar(tmp_path / "arc", "t.tar.gz", ["t/a.md", "t/b.md"])
    rc = main([
        "archive", "--search", r"\.md",
        "--archive-root", str(tmp_path / "arc"),
        "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["archive"] == "t.tar.gz"
    assert set(data[0]["matches"]) == {"t/a.md", "t/b.md"}


def test_065_cli_archive_diger_modlari_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas archive` bayraksız — mevcut '<task> yok' hatası."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "<task> ya da --all ya da --restore" in err

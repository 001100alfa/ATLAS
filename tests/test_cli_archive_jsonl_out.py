"""SPEC 105 — atlas archive --list --json-lines --out PATH testleri."""

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


def test_105_out_yazma_stdout_bos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out PATH → dosya, stdout NDJSON basmaz."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    _mktar(arc, "b.tar.gz", ["x"])
    out = tmp_path / "report.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.is_file()
    stdout = capsys.readouterr().out
    assert not stdout.strip().startswith("{")


def test_105_out_icerik_stdout_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dosya içeriği stdout modu ile AYNI."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    _mktar(arc, "b.tar.gz", ["x"])
    # stdout
    rc = main([
        "archive", "--list", "--json-lines",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    stdout_lines = capsys.readouterr().out.strip().split("\n")
    # --out
    out = tmp_path / "sub" / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    file_lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert file_lines == stdout_lines


def test_105_out_parent_auto_mkdir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    out = tmp_path / "deep" / "nested" / "r.jsonl"
    assert not out.parent.exists()
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    assert out.is_file()


def test_105_out_yazma_hatasi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PATH = mevcut dizin → yazma hatası exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    target = tmp_path / "as_dir"
    target.mkdir()
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(target),
        "--archive-root", str(arc),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err or "yazıl" in err


def test_105_out_jsonl_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out --json-lines yok → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 2


def test_105_115_out_json_artik_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SPEC 115: --out --json artık MUTEX değil (tek JSON dizisi dosyaya)."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    out = tmp_path / "r.json"
    rc = main([
        "archive", "--list", "--json", "--out", str(out),
        "--archive-root", str(arc),
    ])
    assert rc == 0
    import json as _json
    data = _json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list)


def test_105_out_sort_limit_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--sort-by --limit stream öncesi filter → dosyada uygulanmış."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "small.tar.gz", ["x"] * 1)
    _mktar(arc, "big.tar.gz", ["x"] * 100)
    out = tmp_path / "r.jsonl"
    rc = main([
        "archive", "--list", "--json-lines", "--out", str(out),
        "--sort-by", "size", "--desc", "--limit", "1",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    lines = out.read_text(encoding="utf-8").strip().split("\n")
    # 1 arşiv + summary
    assert len(lines) == 2
    assert json.loads(lines[0])["archive"] == "big.tar.gz"


def test_105_out_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out YOK → SPEC 098 stdout AYNI."""
    _env(monkeypatch, tmp_path)
    arc = tmp_path / "arc"
    _mktar(arc, "a.tar.gz", ["x"])
    rc = main([
        "archive", "--list", "--json-lines",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "type" in out and "summary" in out

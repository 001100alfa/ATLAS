"""SPEC 092 — atlas vault verify --format json-lines --out PATH testleri."""

from __future__ import annotations

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


def test_092_out_yazma_stdout_bos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out PATH → dosya yazılır, stdout NDJSON basmaz."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]", "b": "içerik"})
    out = tmp_path / "report.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    # stdout NDJSON içermiyor
    stdout = capsys.readouterr().out
    assert not stdout.strip().startswith("{")


def test_092_out_icerik_stdout_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dosyadaki satırlar stdout modu ile içerik olarak AYNI."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {
        "a": "[[yok1]] [[yok2]]",
        "orfan": "içerik",
    })
    # 1. stdout
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines",
    ])
    assert rc == 0
    stdout_lines = capsys.readouterr().out.strip().split("\n")
    # 2. --out
    out = tmp_path / "sub" / "dir" / "report.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out),
    ])
    assert rc == 0
    file_lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert file_lines == stdout_lines


def test_092_out_parent_dir_olusturulur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Yol'daki ara dizinler otomatik oluşturulur."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    out = tmp_path / "deep" / "nested" / "dir" / "r.jsonl"
    assert not out.parent.exists()
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out),
    ])
    assert rc == 0
    assert out.is_file()
    # Son satır summary
    last = json.loads(out.read_text(encoding="utf-8").strip().split("\n")[-1])
    assert last["type"] == "summary"


def test_092_out_format_json_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out + --format json → SPEC HATASI exit 2."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    out = tmp_path / "r.json"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json", "--out", str(out),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err
    assert "json-lines" in err


def test_092_out_format_human_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out + --format human → exit 2."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    out = tmp_path / "r.txt"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "human", "--out", str(out),
    ])
    assert rc == 2


def test_092_out_format_yok_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out tek başına (format yok) → exit 2."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--out", str(out),
    ])
    assert rc == 2


def test_092_out_strict_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out ile --strict ORTOGONAL: bulgu → dosya yazılır ama exit 4."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    out = tmp_path / "r.jsonl"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out), "--strict",
    ])
    assert rc == 4
    assert out.is_file()
    # Dosya broken_link satırı içermeli
    text = out.read_text(encoding="utf-8")
    assert "broken_link" in text
    assert "summary" in text


def test_092_out_dump_report_ortogonal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out (NDJSON) ile --dump-report (markdown) ikisi de yazılır."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    out = tmp_path / "r.jsonl"
    md = tmp_path / "r.md"
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(out),
        "--dump-report", str(md),
    ])
    assert rc == 0
    assert out.is_file() and md.is_file()
    # NDJSON — her satır JSON
    for ln in out.read_text(encoding="utf-8").strip().split("\n"):
        json.loads(ln)
    # Markdown — # başlık içerir
    assert "#" in md.read_text(encoding="utf-8")


def test_092_out_yazma_hatasi_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PATH yazılamıyor (dosya adı yerine mevcut dizin) → exit 2."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    # Dizin oluştur, path'i o dizinin kendisi yap → open("w") başarısız
    target_dir = tmp_path / "as_dir"
    target_dir.mkdir()
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--out", str(target_dir),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--out" in err or "yazıl" in err


def test_092_out_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--out YOK → SPEC 087 stdout BİT-UYUMLU."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines",
    ])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    for ln in out.split("\n"):
        parsed = json.loads(ln)
        assert "type" in parsed

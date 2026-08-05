"""SPEC 087 — atlas vault verify --format json-lines testleri."""

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


def test_087_jsonl_basic_stream(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """3 kırık link + 2 orfan not → 5 satır bulgu + 1 satır summary."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {
        "a": "[[yok1]] [[yok2]] [[yok3]]",  # 3 kırık
        "orfan1": "içerik",   # link vermeyen ve almayan
        "orfan2": "içerik",
    })
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines",
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    # 3 broken + 3 orphan_note (a de orfan çünkü kırık link'ler sayılmıyor
    # hedef mevcut değil) + summary → değişebilir; kontrol tipi bazlı
    parsed = [json.loads(ln) for ln in lines]
    types = [p["type"] for p in parsed]
    assert types.count("broken_link") == 3
    assert types[-1] == "summary"  # son satır her zaman summary
    summary = parsed[-1]
    assert summary["broken_links"] == 3
    assert summary["clean"] is False


def test_087_jsonl_clean_vault(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Temiz vault → sadece summary satırı, clean=True."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {
        "a": "linkli [[b]] #ortak",
        "b": "linkli [[a]] #ortak",
    })
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines",
    ])
    assert rc == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 1
    summary = json.loads(lines[0])
    assert summary["type"] == "summary"
    assert summary["clean"] is True
    assert summary["notes_total"] == 2
    assert summary["broken_links"] == 0


def test_087_jsonl_ndjson_parseable_each_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Her satır tek başına valid JSON (NDJSON kontratı)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {
        "a": "[[yok]]",
        "b": "içerik",
    })
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # Her satır json.loads ile çözülebilmeli
    for ln in out.strip().split("\n"):
        parsed = json.loads(ln)
        assert "type" in parsed


def test_087_format_json_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format json → tek satır JSON (mevcut --json ile aynı içerik)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]", "b": "içerik"})
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "broken_links" in data
    assert "orphan_notes" in data


def test_087_format_json_pretty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format json-pretty → indent=2 (birden fazla satır)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-pretty",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # Indent'li → çok satırlı
    assert out.count("\n") >= 3
    # Yine valid JSON
    data = json.loads(out)
    assert "broken_links" in data


def test_087_format_json_yerine_json_bayragi_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format + --json → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--json",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "MUTEX" in err or "birlikte" in err


def test_087_format_pretty_bayrak_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format + --pretty → MUTEX exit 2."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json", "--pretty",
    ])
    assert rc == 2


def test_087_jsonl_gecersiz_choice(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format geçersiz → argparse SystemExit(2)."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "içerik"})
    with pytest.raises(SystemExit) as ei:
        main([
            "vault", "verify", "--vault-root", str(v),
            "--format", "yaml",
        ])
    assert ei.value.code == 2


def test_087_jsonl_strict_ile_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format json-lines --strict → bulgu varsa exit 4."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]"})
    rc = main([
        "vault", "verify", "--vault-root", str(v),
        "--format", "json-lines", "--strict",
    ])
    assert rc == 4


def test_087_format_yoksa_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format VERİLMEZSE + --json → SPEC 042 aynı çıktı."""
    _env(monkeypatch, tmp_path)
    v = tmp_path / "v"
    _make_vault(v, {"a": "[[yok]]", "b": "içerik"})
    rc = main([
        "vault", "verify", "--vault-root", str(v), "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "broken_links" in data

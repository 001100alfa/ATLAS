"""SPEC 172 — atlas vault verify --schema --format json-lines testleri."""

from __future__ import annotations

import gzip
import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def _lines(stdout: str) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def _cmd(*extra):
    return [
        "vault", "verify", "--schema", "--format", "json-lines",
        "--vault-root", "yok",
        *extra,
    ]


def test_172_jsonl_stream_temel(monkeypatch, tmp_path, capsys):
    """NDJSON stream; son satır summary; tipler var."""
    _env(monkeypatch, tmp_path)
    rc = main(_cmd())
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    assert lines[-1]["type"] == "summary"
    assert lines[-1]["schema_version"] == "1"
    types = {ln["type"] for ln in lines[:-1]}
    assert "top_level" in types
    assert "exit_code" in types
    assert "format" in types


def test_172_jsonl_summary_sayilari(monkeypatch, tmp_path, capsys):
    """summary sayıları stream tip dağılımına eşit."""
    _env(monkeypatch, tmp_path)
    rc = main(_cmd())
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    summary = lines[-1]
    body = lines[:-1]
    counts: dict[str, int] = {}
    for ln in body:
        counts[ln["type"]] = counts.get(ln["type"], 0) + 1
    assert counts.get("top_level", 0) == summary["top_level_count"]
    assert counts.get("exit_code", 0) == summary["exit_codes_count"]
    assert counts.get("format", 0) == summary["formats_count"]


def test_172_jsonl_top_level_alanlari(monkeypatch, tmp_path, capsys):
    """SPEC 136 6 top_level alan NDJSON satırlarında görünür."""
    _env(monkeypatch, tmp_path)
    rc = main(_cmd())
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    tl = [ln for ln in lines if ln.get("type") == "top_level"]
    names = {ln["name"] for ln in tl}
    for expected in ("notes_total", "links_total", "tags_total",
                     "broken_links", "orphan_notes", "orphan_tags"):
        assert expected in names


def test_172_jsonl_out_yazar(monkeypatch, tmp_path, capsys):
    """--out ile PATH'e stream; stdout boş."""
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "vault-verify-schema.jsonl"
    rc = main(_cmd("--out", str(out_path)))
    assert rc == 0
    assert capsys.readouterr().out == ""
    assert out_path.is_file()
    lines = _lines(out_path.read_text(encoding="utf-8"))
    assert lines[-1]["type"] == "summary"


def test_172_jsonl_out_gzip_auto_suffix(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    out_path = tmp_path / "vault-verify-schema.jsonl"
    rc = main(_cmd("--out", str(out_path), "--gzip"))
    assert rc == 0
    gz_path = out_path.with_suffix(out_path.suffix + ".gz")
    assert gz_path.is_file()
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        text = fh.read()
    assert '"type": "summary"' in text


def test_172_gzip_out_yoksa_hata(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(_cmd("--gzip"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_172_schema_yok_normal_json_lines_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 087 --format json-lines NORMAL modda bulgu stream — SPEC 172
    yalnız --schema ile ayrı dal (yeni SPEC 172 bit-uyumlu)."""
    _env(monkeypatch, tmp_path)
    # Vault yoksa SPEC 087 normal verify SPEC HATASI verir (vault dizini yok).
    rc = main([
        "vault", "verify", "--format", "json-lines",
        "--vault-root", str(tmp_path / "kesinlikle-yok"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "vault dizini yok" in err
    # Yani SPEC 087 normal davranış AYNI: schema ayrı, normal ayrı.


def test_172_schema_json_default_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format YOK → SPEC 136 JSON default AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"
    assert "top_level" in data


def test_172_schema_prometheus_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 140 --format prometheus çıktısı AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "vault", "verify", "--schema", "--format", "prometheus",
        "--vault-root", "yok",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "atlas_vault_verify_schema_version" in out
    assert "# HELP" in out

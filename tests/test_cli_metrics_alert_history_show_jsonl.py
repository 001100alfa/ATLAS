"""SPEC 184 — metrics --alert-history-show --format json-lines testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    hist = tmp_path / "alert-history.jsonl"
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "yok.jsonl"))
    monkeypatch.chdir(tmp_path)
    return hist


def _seed_history(path: Path, count: int = 2) -> None:
    records = [
        {"ts": f"2026-08-10T12:0{i}:00", "alert": "cache-hit",
         "hit_ratio_pct": 10.0 + i, "threshold_pct": 30.0,
         "records": 50, "tokens_in": 1000, "tokens_out": 500,
         "cache_creation": 0, "cache_read": 100 * i,
         "channels": ["webhook"]}
        for i in range(count)
    ]
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def _lines(stdout: str) -> list[dict]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def test_184_format_jsonl_ndjson_stream(monkeypatch, tmp_path, capsys):
    """--format json-lines NDJSON stream + summary satırı."""
    hist = _env(monkeypatch, tmp_path)
    _seed_history(hist, count=3)
    rc = main([
        "metrics", "--alert-history-show", str(hist),
        "--format", "json-lines",
    ])
    assert rc == 0
    lines = _lines(capsys.readouterr().out)
    # 3 record + 1 summary
    assert len(lines) == 4
    assert lines[-1]["type"] == "summary"
    assert lines[-1]["total"] == 3
    assert lines[-1]["count"] == 3


def test_184_format_jsonl_ile_json_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--format json-lines çıktısı --json çıktısı ile birebir aynı."""
    hist = _env(monkeypatch, tmp_path)
    _seed_history(hist, count=2)
    # --json çıktısı
    rc = main(["metrics", "--alert-history-show", str(hist), "--json"])
    assert rc == 0
    json_out = capsys.readouterr().out
    # --format json-lines çıktısı
    rc = main([
        "metrics", "--alert-history-show", str(hist),
        "--format", "json-lines",
    ])
    assert rc == 0
    fmt_out = capsys.readouterr().out
    assert json_out == fmt_out


def test_184_json_jsonl_mutex(monkeypatch, tmp_path, capsys):
    """--json + --format json-lines → argparse mutex exit 2."""
    hist = _env(monkeypatch, tmp_path)
    _seed_history(hist, count=1)
    # p_met_out mutually_exclusive_group: --json vs --format
    # argparse SystemExit(2) atar
    with pytest.raises(SystemExit) as exc:
        main([
            "metrics", "--alert-history-show", str(hist),
            "--json", "--format", "json-lines",
        ])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "not allowed" in err or "--format" in err


def test_184_format_jsonl_out(monkeypatch, tmp_path, capsys):
    """--format json-lines --out PATH dosyaya stream, stdout boş."""
    hist = _env(monkeypatch, tmp_path)
    _seed_history(hist, count=2)
    out_path = tmp_path / "alert-hist.jsonl"
    rc = main([
        "metrics", "--alert-history-show", str(hist),
        "--format", "json-lines", "--out", str(out_path),
    ])
    assert rc == 0
    assert capsys.readouterr().out == ""
    assert out_path.is_file()
    lines = _lines(out_path.read_text(encoding="utf-8"))
    assert len(lines) == 3  # 2 record + 1 summary
    assert lines[-1]["type"] == "summary"


def test_184_normal_metrics_format_jsonl_reddet(monkeypatch, tmp_path, capsys):
    """`--format json-lines` normal metrics (--alert-history-show yok) → exit 2."""
    _env(monkeypatch, tmp_path)
    rc = main(["metrics", "--format", "json-lines"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "json-lines" in err
    assert "--alert-history-show" in err


def test_184_out_yalniz_json_jsonl_prom(monkeypatch, tmp_path, capsys):
    """--out yalnız --json/--format json-lines/prometheus ile
    (human modda reddet)."""
    hist = _env(monkeypatch, tmp_path)
    _seed_history(hist, count=1)
    rc = main([
        "metrics", "--alert-history-show", str(hist),
        "--out", str(tmp_path / "x.txt"),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--out" in err


def test_184_strict_ile_ortogonal(monkeypatch, tmp_path, capsys):
    """--format json-lines + --strict → NDJSON basılır + exit 4 (SPEC 148)."""
    hist = _env(monkeypatch, tmp_path)
    _seed_history(hist, count=1)
    rc = main([
        "metrics", "--alert-history-show", str(hist),
        "--format", "json-lines", "--strict",
    ])
    assert rc == 4  # SPEC 148
    lines = _lines(capsys.readouterr().out)
    assert lines[-1]["type"] == "summary"


def test_184_schema_json_lines_formats_alaninda(monkeypatch, tmp_path, capsys):
    """SPEC 179 schema `formats` alanında `json-lines` (SPEC 184) var."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "metrics", "--alert-history-show", str(tmp_path / "yok.jsonl"),
        "--schema",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    fmt_names = {f["name"] for f in data["formats"]}
    assert "json-lines" in fmt_names
    by_name = {f["name"]: f for f in data["formats"]}
    assert by_name["json-lines"]["spec"] == "184"

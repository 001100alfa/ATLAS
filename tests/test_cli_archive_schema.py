"""SPEC 149 — atlas archive --schema testleri."""

from __future__ import annotations

import json

from atlas_core.cli import main


def test_149_schema_kisa_devre(monkeypatch, tmp_path, capsys):
    """--schema → arşiv kökü gerekmez, JSON şema basılır."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["archive", "--schema", "--archive-root", "yok"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["schema_version"] == "1"
    assert "top_level" in data
    assert "exit_codes" in data
    assert "formats" in data


def test_149_schema_top_level_7_alan(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [f["name"] for f in data["top_level"]]
    for f in ("archive", "task_id", "date", "size_bytes",
              "size_human", "member_count", "mtime"):
        assert f in names
    assert len(data["top_level"]) == 7


def test_149_schema_exit_codes(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    for code in ("0", "2", "3", "6"):
        assert code in data["exit_codes"]


def test_149_schema_formats(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    fmt_names = [f["name"] for f in data["formats"]]
    for fmt in ("human", "json", "json-lines"):
        assert fmt in fmt_names


def test_149_schema_pretty(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["archive", "--schema", "--pretty"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.count("\n") >= 5
    data = json.loads(out)
    assert "schema_version" in data


def test_149_schema_notes_referanslar(monkeypatch, tmp_path, capsys):
    """notes: SPEC 079/085/093/105/108/127/133/138/149 referansları."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.chdir(tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    notes_text = "\n".join(data["notes"])
    for spec in ("SPEC 079", "SPEC 085", "SPEC 093", "SPEC 105",
                 "SPEC 108", "SPEC 127", "SPEC 133", "SPEC 138",
                 "SPEC 149"):
        assert spec in notes_text


def test_149_schema_yoksa_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """--schema YOK + geçerli --list → SPEC 075 çıktısı AYNI."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.chdir(tmp_path)
    arc = tmp_path / "arc"
    arc.mkdir()
    rc = main([
        "archive", "--list",
        "--archive-root", str(arc),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(arsiv yok)" in out

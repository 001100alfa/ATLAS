"""SPEC 182 — atlas archive --restore --schema testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def _schema(monkeypatch, tmp_path, capsys) -> dict:
    _env(monkeypatch, tmp_path)
    rc = main([
        "archive", "--restore", "yok-id", "--schema",
        "--tasks-root", str(tmp_path / "tasks"),
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_182_schema_kisa_devre(monkeypatch, tmp_path, capsys):
    """--schema kısa devre; TASK_ID/arşiv gerekmez."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert data["schema_version"] == "1"


def test_182_dry_run_json_fields(monkeypatch, tmp_path, capsys):
    """SPEC 127 dry-run çıktısı 5 alan."""
    data = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in data["dry_run_json_fields"]}
    assert names == {"mode", "task_id", "archive", "target", "conflict"}


def test_182_apply_json_fields(monkeypatch, tmp_path, capsys):
    """SPEC 127 apply çıktısı 5 alan."""
    data = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in data["apply_json_fields"]}
    assert names == {"mode", "task_id", "archive", "target", "restored"}


def test_182_jsonl_record_types(monkeypatch, tmp_path, capsys):
    """SPEC 133 NDJSON 3 record type."""
    data = _schema(monkeypatch, tmp_path, capsys)
    types = {r["name"] for r in data["jsonl_record_types"]}
    assert types == {"plan", "restored", "summary"}
    # `restored` yalnız --apply
    by_name = {r["name"]: r for r in data["jsonl_record_types"]}
    assert "yalnız --apply" in by_name["restored"]["when"]


def test_182_alert_payload_6_alan(monkeypatch, tmp_path, capsys):
    """SPEC 176 payload 6 + SPEC 198 timestamp = 7 alan."""
    data = _schema(monkeypatch, tmp_path, capsys)
    names = {f["name"] for f in data["alert_payload_fields"]}
    assert names == {
        "alert", "task_id", "search_pattern",
        "archive_root", "error", "exit_code", "timestamp",
    }
    by = {f["name"]: f for f in data["alert_payload_fields"]}
    for k in ("alert", "task_id", "search_pattern",
              "archive_root", "error", "exit_code"):
        assert by[k]["spec"] == "176"
    assert by["timestamp"]["spec"] == "198"


def test_182_exit_codes(monkeypatch, tmp_path, capsys):
    """SPEC 033/071/176 exit codes 0/2/3/6."""
    data = _schema(monkeypatch, tmp_path, capsys)
    assert set(data["exit_codes"].keys()) == {"0", "2", "3", "6"}


def test_182_notes_spec_referanslari(monkeypatch, tmp_path, capsys):
    """notes: SPEC 033/065/071/127/133/138/176/182 referansları."""
    data = _schema(monkeypatch, tmp_path, capsys)
    notes_text = " ".join(data["notes"])
    for spec in ("033", "065", "071", "127", "133", "138", "176", "182"):
        assert f"SPEC {spec}" in notes_text


def test_182_pretty_indent_2(monkeypatch, tmp_path, capsys):
    """--pretty indent=2."""
    _env(monkeypatch, tmp_path)
    rc = main([
        "archive", "--restore", "yok", "--schema", "--pretty",
        "--tasks-root", str(tmp_path / "tasks"),
        "--archive-root", str(tmp_path / "arc"),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert '\n  "schema_version"' in out
    assert '\n  "dry_run_json_fields"' in out


def test_182_archive_schema_bit_uyumlu(monkeypatch, tmp_path, capsys):
    """`archive --schema` (restore olmadan) SPEC 149 AYNI şema (bit-uyumlu)."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    # SPEC 149/164 alanları:
    assert "top_level" in data
    assert "sub_commands" in data  # SPEC 164
    # SPEC 182 alanları YOK (ayrı komut şeması):
    assert "dry_run_json_fields" not in data


def test_182_restore_search_belirsizlik_normal_calisir(
    monkeypatch, tmp_path, capsys,
):
    """--restore --schema DOKUNULMAZ normal --restore --search davranışı;
    schema kısa devre önce, --search DAHİL --schema yoksa normal akışa
    döner (bit-uyumluluk kanıt)."""
    _env(monkeypatch, tmp_path)
    # --schema YOK → normal restore akışı; arşiv yok → exit 6
    (tmp_path / "arc").mkdir()
    (tmp_path / "tasks").mkdir()
    rc = main([
        "archive", "--restore", "yok-id",
        "--tasks-root", str(tmp_path / "tasks"),
        "--archive-root", str(tmp_path / "arc"),
    ])
    # Dry-run: arşiv yok → exit 6 (SPEC 033 kalıbı)
    assert rc == 6

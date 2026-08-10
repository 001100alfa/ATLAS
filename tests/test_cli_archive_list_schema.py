"""SPEC 164 — atlas archive --list --schema + sub_commands testleri."""

from __future__ import annotations

import json

import pytest

from atlas_core.cli import main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))


def test_164_sub_commands_alani_var(monkeypatch, tmp_path, capsys):
    """SPEC 164: JSON schema'da `sub_commands` alanı var."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert "sub_commands" in data
    assert set(data["sub_commands"].keys()) == {"list", "restore", "search", "all"}


def test_164_sub_commands_list_exit_codes(monkeypatch, tmp_path, capsys):
    """list yalnız 0/2 çıkarır (read-only bilgi)."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["sub_commands"]["list"]["exit_codes"] == ["0", "2"]
    assert data["sub_commands"]["list"]["spec"] == "075"


def test_164_sub_commands_restore_exit_codes(monkeypatch, tmp_path, capsys):
    """restore 0/2/3/6 çıkarır (çakışma + extract hatası dahil)."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["sub_commands"]["restore"]["exit_codes"] == ["0", "2", "3", "6"]
    assert data["sub_commands"]["restore"]["spec"] == "033"


def test_164_sub_commands_search_all(monkeypatch, tmp_path, capsys):
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["sub_commands"]["search"]["exit_codes"] == ["0", "2"]
    assert data["sub_commands"]["all"]["exit_codes"] == ["0", "2"]


def test_164_archive_list_schema_ayni_cikti(monkeypatch, tmp_path, capsys):
    """`archive --list --schema` = `archive --schema` bit-uyumlu."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    schema_only = capsys.readouterr().out
    rc = main(["archive", "--list", "--schema"])
    assert rc == 0
    list_schema = capsys.readouterr().out
    assert schema_only == list_schema


def test_164_archive_list_schema_pretty(monkeypatch, tmp_path, capsys):
    """`archive --list --schema --pretty` indent=2 çalışır."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--list", "--schema", "--pretty"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '\n  "schema_version"' in out
    assert '\n  "sub_commands"' in out


def test_164_prometheus_sub_commands_yok(monkeypatch, tmp_path, capsys):
    """SPEC 164: Prometheus çıktısında sub_commands YOK (YAGNI)."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema", "--format", "prometheus"])
    assert rc == 0
    out = capsys.readouterr().out
    # Yeni metric aile eklenmedi:
    assert "atlas_archive_schema_sub_command" not in out
    # Mevcut 4 metric ailesi sayısı korunuyor:
    assert out.count("# HELP atlas_archive_schema_") == 4


def test_164_mevcut_top_level_dokunulmadi(monkeypatch, tmp_path, capsys):
    """SPEC 149 mevcut top_level 7 alan AYNI."""
    _env(monkeypatch, tmp_path)
    rc = main(["archive", "--schema"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [f["name"] for f in data["top_level"]]
    assert names == ["archive", "task_id", "date", "size_bytes",
                     "size_human", "member_count", "mtime"]
    # Mevcut exit_codes tüm alt komutları kapsar (0/2/3/6)
    assert set(data["exit_codes"].keys()) == {"0", "2", "3", "6"}

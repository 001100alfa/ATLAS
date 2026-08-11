"""SPEC 200 — schema notes'a timestamp SPEC referansları."""

from __future__ import annotations

import json

from atlas_core.cli import main


def _archive(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["archive", "--schema"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def _vault_backup(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["vault", "backup", "--schema", "--vault-root", "yok"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def _vault_verify(monkeypatch, tmp_path, capsys) -> dict:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    rc = main(["vault", "verify", "--schema", "--vault-root", "yok"])
    assert rc == 0
    return json.loads(capsys.readouterr().out.strip())


def test_200_archive_notes_spec_198_200(monkeypatch, tmp_path, capsys):
    d = _archive(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    assert "SPEC 198" in text
    assert "SPEC 200" in text


def test_200_vault_backup_notes_spec_199_200(monkeypatch, tmp_path, capsys):
    d = _vault_backup(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    assert "SPEC 199" in text
    assert "SPEC 200" in text


def test_200_vault_verify_notes_spec_200(monkeypatch, tmp_path, capsys):
    d = _vault_verify(monkeypatch, tmp_path, capsys)
    text = " ".join(d["notes"])
    assert "SPEC 186" in text
    assert "SPEC 200" in text

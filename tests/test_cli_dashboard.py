"""SPEC 024 — atlas dashboard testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main
from atlas_core.security.audit import AuditLog


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "metrics.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))


def test_024_bos_audit_exit_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Audit dosyası yoksa `(0 run)` mesajı + exit 0."""
    _env(monkeypatch, tmp_path)
    rc = main(["dashboard"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(0 run)" in out
    assert "denetim zinciri:" in out


def test_024_tek_done_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Bir tam done run."""
    _env(monkeypatch, tmp_path)
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditLog(audit_path)
    audit.record("atlas-run", "plan", "write:x.txt:1")
    audit.record("atlas-run", "observe", "wrote 1")
    audit.record("atlas-run", "done", "hedef")

    rc = main(["dashboard"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "GEÇERLİ" in out
    assert "done" in out
    assert "1" in out  # steps=1


def test_024_max_steps_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _env(monkeypatch, tmp_path)
    audit = AuditLog(tmp_path / "audit.jsonl")
    audit.record("atlas-run", "plan", "p1")
    audit.record("atlas-run", "plan", "p2")
    audit.record("atlas-run", "plan", "p3")
    audit.record("atlas-run", "max_steps", "hedef")
    rc = main(["dashboard"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "max_steps" in out
    assert "3" in out  # 3 plan


def test_024_llm_error_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _env(monkeypatch, tmp_path)
    audit = AuditLog(tmp_path / "audit.jsonl")
    audit.record("atlas-run", "plan", "p1")
    audit.record("atlas-run", "llm_error", "timeout")
    rc = main(["dashboard"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "llm_error" in out


def test_024_json_cikti(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--json çıktı yapısı."""
    _env(monkeypatch, tmp_path)
    audit = AuditLog(tmp_path / "audit.jsonl")
    audit.record("atlas-run", "plan", "p1")
    audit.record("atlas-run", "done", "hedef")

    rc = main(["dashboard", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["audit_chain_valid"] is True
    assert len(data["runs"]) == 1
    assert data["runs"][0]["exit"] == "done"


def test_024_cost_run_araligindan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Metrics.jsonl'daki ts run zaman aralığındaysa cost hesaplanır."""
    _env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15")
    audit = AuditLog(tmp_path / "audit.jsonl")
    audit.record("atlas-run", "plan", "p1")
    audit.record("atlas-run", "done", "hedef")

    # metrics dosyası — run zaman aralığında bir kayıt
    # audit'te ts UTC ISO; metrics'te de aynı format
    metrics_path = tmp_path / "metrics.jsonl"
    # audit'ten tam TS okuyup metrics'e koyalım
    audit_line = json.loads(
        (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    metrics_path.write_text(
        json.dumps({
            "ts": audit_line["ts"],
            "in": 1_000_000, "out": 200_000,
            "cache_c": 0, "cache_r": 0,
            "cost": "?",
        }) + "\n",
        encoding="utf-8",
    )
    rc = main(["dashboard", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    # 1M in * 3 + 200k out * 15 = 3 + 3 = 6
    assert data["runs"][0]["cost"] == "$6.000000"

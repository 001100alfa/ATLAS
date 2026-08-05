"""SPEC 072 — atlas run --estimate --adaptive metrics ortalaması."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import _read_metrics_avg_tokens, main


def _make_goal_yaml(tmp_path: Path, name: str = "g", max_steps: int = 8) -> Path:
    p = tmp_path / f"{name}.yaml"
    p.write_text(
        f"goal: hedef {name}\n"
        f"plan_kind: static\n"
        f"plan_steps:\n"
        f'  - "write:x.txt:hi"\n'
        f"action_allowlist: [write]\n"
        f"judge_kind: file_exists\n"
        f'judge_arg: "x.txt"\n'
        f"budget: 50\n"
        f"max_steps: {max_steps}\n",
        encoding="utf-8",
    )
    return p


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.delenv("ATLAS_ESTIMATE_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("ATLAS_LLM_PRICE_IN_PER_1M", raising=False)
    monkeypatch.delenv("ATLAS_LLM_PRICE_OUT_PER_1M", raising=False)
    return metrics


def _write_metrics(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


# ═════════════════════════════════════════════════════════════════════
# _read_metrics_avg_tokens (birim)
# ═════════════════════════════════════════════════════════════════════


def test_072_metrics_yok_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    avg, n = _read_metrics_avg_tokens(20)
    assert avg is None
    assert n == 0


def test_072_metrics_az_kayit_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """< 3 kayıt → None (yeterli numune yok)."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "t", "in": 100, "out": 50},
        {"ts": "t", "in": 200, "out": 100},
    ])
    avg, n = _read_metrics_avg_tokens(20)
    assert avg is None
    assert n == 2


def test_072_metrics_ortalama_hesaplanir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """3+ kayıt → in+out+cache toplamının ortalaması."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "t1", "in": 100, "out": 50, "cache_c": 20, "cache_r": 30},
        {"ts": "t2", "in": 200, "out": 100, "cache_c": 0, "cache_r": 0},
        {"ts": "t3", "in": 300, "out": 200, "cache_c": 0, "cache_r": 0},
    ])
    # Toplam call'lar: 200, 300, 500 → sum=1000, n=3, avg=333
    avg, n = _read_metrics_avg_tokens(20)
    assert n == 3
    assert avg == 333  # 1000 // 3


def test_072_metrics_limit_uygulanir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """limit N → sadece son N kayıt sayılır."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "t", "in": 1000, "out": 0} for _ in range(5)
    ] + [
        {"ts": "t", "in": 100, "out": 0} for _ in range(3)
    ])
    # limit=3: son 3 kayıt = 100 tokens/call; avg=100
    avg, n = _read_metrics_avg_tokens(3)
    assert n == 3
    assert avg == 100


# ═════════════════════════════════════════════════════════════════════
# CLI --estimate --adaptive
# ═════════════════════════════════════════════════════════════════════


def test_072_cli_adaptive_metrics_kullanir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--adaptive + yeterli metrics → source=adaptive-avg."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "t", "in": 200, "out": 100},
        {"ts": "t", "in": 200, "out": 100},
        {"ts": "t", "in": 200, "out": 100},
    ])  # avg = 300 tokens/call
    goal = _make_goal_yaml(tmp_path, max_steps=4)
    rc = main([
        "run", "--goal-file", str(goal),
        "--estimate", "--adaptive", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["source"] == "adaptive-avg"
    assert data["sample_count"] == 3
    assert data["tokens_per_call"] == 300
    assert data["estimated_total_tokens"] == 1200  # 4 * 300


def test_072_cli_adaptive_az_kayit_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--adaptive + < 3 kayıt → static fallback + UYARI."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "t", "in": 100, "out": 50},
    ])  # sadece 1 kayıt
    goal = _make_goal_yaml(tmp_path)
    rc = main([
        "run", "--goal-file", str(goal),
        "--estimate", "--adaptive", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["source"] == "adaptive-fallback-static"
    assert data["tokens_per_call"] == 500  # env default


def test_072_cli_adaptive_metrics_yok_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--adaptive + metrics.jsonl yok → static fallback."""
    _env(monkeypatch, tmp_path)
    # metrics dosyası oluşturulmadı
    goal = _make_goal_yaml(tmp_path)
    rc = main([
        "run", "--goal-file", str(goal),
        "--estimate", "--adaptive", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["source"] == "adaptive-fallback-static"
    assert data["sample_count"] == 0


def test_072_cli_adaptive_n_ozel_deger(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--adaptive-n 5 → son 5 kayıt kullanılır."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [
        {"ts": "t", "in": 1000, "out": 0}  # 1000 token/call — eski
        for _ in range(10)
    ] + [
        {"ts": "t", "in": 100, "out": 0}   # 100 token/call — yeni
        for _ in range(5)
    ])
    goal = _make_goal_yaml(tmp_path)
    rc = main([
        "run", "--goal-file", str(goal),
        "--estimate", "--adaptive", "--adaptive-n", "5", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tokens_per_call"] == 100  # son 5 avg


def test_072_cli_adaptive_insan_ciktisi_source_gorunur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """İnsan çıktısı `source: adaptive-avg, n=3` gösterir."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}] * 3)
    goal = _make_goal_yaml(tmp_path)
    rc = main([
        "run", "--goal-file", str(goal),
        "--estimate", "--adaptive",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "source: adaptive-avg" in out
    assert "n=3" in out


def test_072_cli_estimate_static_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--estimate (adaptive YOK) → SPEC 069 static, source=static."""
    _env(monkeypatch, tmp_path)
    goal = _make_goal_yaml(tmp_path, max_steps=5)
    rc = main([
        "run", "--goal-file", str(goal), "--estimate", "--json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["source"] == "static"
    assert data["tokens_per_call"] == 500
    assert data["sample_count"] == 0

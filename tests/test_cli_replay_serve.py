"""SPEC 055 — atlas replay --serve HOST:PORT JSON HTTP endpoint."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from atlas_core.cli import _build_replay_json_body, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test env: `.atlas/runs/` dizini tmp_path altında."""
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_METRICS", str(tmp_path / "m.jsonl"))
    monkeypatch.chdir(tmp_path)


def _mkrun(tmp_path: Path, run_id: str, goal: str = "test goal") -> Path:
    """Sahte `.atlas/runs/<run_id>.yaml` üret."""
    runs_dir = tmp_path / ".atlas" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = runs_dir / f"{run_id}.yaml"
    yaml_path.write_text(f"goal: {goal}\nsteps: []\n", encoding="utf-8")
    return yaml_path


# ═════════════════════════════════════════════════════════════════════
# _build_replay_json_body (birim)
# ═════════════════════════════════════════════════════════════════════


def test_055_build_body_bos_liste_json_dizi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    body = _build_replay_json_body(limit=10)
    data = json.loads(body)
    assert data == []


def test_055_build_body_kayit_var_dizi_dolu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    _env(monkeypatch, tmp_path)
    _mkrun(tmp_path, "20260804-120000", goal="ilk")
    _mkrun(tmp_path, "20260804-130000", goal="ikinci")

    body = _build_replay_json_body(limit=10)
    data = json.loads(body)
    assert len(data) == 2
    # Her kayıt run_id + mtime + goal
    for r in data:
        assert set(r.keys()) >= {"run_id", "mtime", "goal"}
    ids = {r["run_id"] for r in data}
    assert ids == {"20260804-120000", "20260804-130000"}


def test_055_build_body_limit_uygulanir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Limit N → en yeni N kayıt."""
    _env(monkeypatch, tmp_path)
    for i in range(5):
        _mkrun(tmp_path, f"run-{i}")

    body = _build_replay_json_body(limit=3)
    data = json.loads(body)
    assert len(data) == 3


# ═════════════════════════════════════════════════════════════════════
# HTTP entegrasyon — gerçek istek
# ═════════════════════════════════════════════════════════════════════


def _run_serve_and_probe(argv: list[str], path: str = "/runs"):
    """`main(argv)` blocking + ready_cb ile probe (SPEC 051 kalıbı)."""
    from atlas_core.observability import prometheus_server as ps

    result: dict = {}
    real_serve = ps.serve_prometheus_http

    def wrap_serve(host, port, body_fn, **kw):
        def ready(server):
            actual_port = server.server_address[1]
            time.sleep(0.05)
            try:
                url = f"http://127.0.0.1:{actual_port}{path}"
                with urllib.request.urlopen(url, timeout=2.0) as resp:  # noqa: S310
                    result["status"] = resp.status
                    result["body"] = resp.read().decode("utf-8")
                    result["content_type"] = resp.headers.get("Content-Type")
            except Exception as exc:  # noqa: BLE001
                result["error"] = str(exc)
            finally:
                threading.Thread(
                    target=server.shutdown, daemon=True,
                ).start()

        return real_serve(host, port, body_fn, ready_cb=ready, **kw)

    ps.serve_prometheus_http = wrap_serve
    try:
        rc = main(argv)
    finally:
        ps.serve_prometheus_http = real_serve
    return rc, result


def test_055_cli_serve_json_endpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`atlas replay --serve :0` → JSON dizi + application/json."""
    _env(monkeypatch, tmp_path)
    _mkrun(tmp_path, "run-1", goal="dev")

    rc, r = _run_serve_and_probe(["replay", "--serve", ":0"])
    assert rc == 0
    assert r["status"] == 200
    assert "application/json" in r["content_type"]
    data = json.loads(r["body"])
    assert isinstance(data, list)
    assert data[0]["run_id"] == "run-1"


def test_055_cli_serve_root_ve_runs_endpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`GET /` de aynı JSON döner (kolaylık path)."""
    _env(monkeypatch, tmp_path)
    _mkrun(tmp_path, "run-1")

    # GET / probe
    rc, r = _run_serve_and_probe(["replay", "--serve", ":0"], path="/")
    assert rc == 0
    assert r["status"] == 200
    assert "application/json" in r["content_type"]


def test_055_cli_serve_metrics_path_404(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """`GET /metrics` replay serve'de KABUL DEĞİL (yalnız / veya /runs)."""
    _env(monkeypatch, tmp_path)
    _mkrun(tmp_path, "run-1")

    rc, r = _run_serve_and_probe(["replay", "--serve", ":0"], path="/metrics")
    assert rc == 0
    assert r.get("error", "") != ""
    # urllib HTTPError 404
    assert "404" in r.get("error", "")


# ═════════════════════════════════════════════════════════════════════
# CLI mutex + hata yolları
# ═════════════════════════════════════════════════════════════════════


def test_055_cli_serve_list_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["replay", "--serve", ":9092", "--list"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--serve ve --list" in err


def test_055_cli_serve_run_id_mutex(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["replay", "some-run-id", "--serve", ":9092"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "run-id verilemez" in err


def test_055_cli_serve_gecersiz_port_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _env(monkeypatch, tmp_path)
    rc = main(["replay", "--serve", "abc"])  # : yok
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_055_cli_replay_default_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--serve` yoksa mevcut davranış (SPEC 027/028)."""
    _env(monkeypatch, tmp_path)
    # --list yoluyla mevcut bit-uyumlu davranış
    rc = main(["replay", "--list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(hiç kayıt yok)" in out or "kayıtlı" in out

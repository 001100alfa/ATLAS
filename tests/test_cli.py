"""Platform giriş noktası (atlas CLI) uçtan uca testleri.

Beyin + orkestratör + güvenlik katmanlarının tek arayüzden birlikte
çalıştığını doğrular. Yollar ATLAS_VAULT / ATLAS_AUDIT ile izole edilir.
"""
from pathlib import Path

import pytest

from atlas_core import cli


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "vault"))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "audit.jsonl"))
    return tmp_path


def test_remember_ve_recall(env: Path, capsys: pytest.CaptureFixture[str]):
    assert cli.main(["remember", "kesit", "atalet momenti", "--link", "EN1993"]) == 0
    assert cli.main(["recall", "atalet"]) == 0
    out = capsys.readouterr().out
    assert "kesit" in out


def test_run_dongusu_ve_audit(env: Path, capsys: pytest.CaptureFixture[str]):
    rc = cli.main(["run", "hedef", "--steps", "2", "--budget", "50"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "done=True" in out
    # Döngü audit'e yazdı -> zincir doğrulanabilir olmalı
    assert cli.main(["audit-verify"]) == 0


def test_run_butce_asimi(env: Path):
    # 3 adım x 100 maliyet, bütçe 50 -> ilk adımda aşım (çıkış kodu 3)
    rc = cli.main(["run", "hedef", "--steps", "3", "--budget", "50", "--step-cost", "100"])
    assert rc == 3


def test_scan_sir_bulur(env: Path, tmp_path: Path):
    leaky = tmp_path / "leak.py"
    leaky.write_text('api_key = "SUPERSECRET_TOKEN_1234"\n', encoding="utf-8")
    assert cli.main(["scan", str(leaky)]) == 1


def test_scan_temiz(env: Path, tmp_path: Path):
    clean = tmp_path / "clean.py"
    clean.write_text("x = 1\n", encoding="utf-8")
    assert cli.main(["scan", str(clean)]) == 0


def test_context_bos(env: Path, capsys: pytest.CaptureFixture[str]):
    assert cli.main(["context", "bilinmeyen konu"]) == 0
    assert "kayıtlı bağlam yok" in capsys.readouterr().out

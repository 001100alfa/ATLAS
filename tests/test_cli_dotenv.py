"""SPEC 022 — `.env` otomatik yükleme testleri."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from atlas_core.cli import _load_dotenv, main


def test_022_dosya_yok_no_op(tmp_path: Path) -> None:
    """Dosya yoksa 0 yüklenir, hata yok."""
    assert _load_dotenv(tmp_path / "yok.env") == 0


def test_022_basit_key_val(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """KEY=VAL basit format."""
    monkeypatch.delenv("TEST_KEY_A", raising=False)
    envfile = tmp_path / ".env"
    envfile.write_text("TEST_KEY_A=abc\n", encoding="utf-8")
    n = _load_dotenv(envfile)
    assert n == 1
    assert os.environ["TEST_KEY_A"] == "abc"
    monkeypatch.delenv("TEST_KEY_A", raising=False)


def test_022_tirnak_siyrilir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`"..."` ve `'...'` tırnaklı değerler sıyrılır."""
    monkeypatch.delenv("TEST_KEY_B", raising=False)
    monkeypatch.delenv("TEST_KEY_C", raising=False)
    envfile = tmp_path / ".env"
    envfile.write_text(
        'TEST_KEY_B="çift tırnak"\n'
        "TEST_KEY_C='tek tırnak'\n",
        encoding="utf-8",
    )
    _load_dotenv(envfile)
    assert os.environ["TEST_KEY_B"] == "çift tırnak"
    assert os.environ["TEST_KEY_C"] == "tek tırnak"
    monkeypatch.delenv("TEST_KEY_B", raising=False)
    monkeypatch.delenv("TEST_KEY_C", raising=False)


def test_022_override_etmez(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mevcut env değişkeni **override edilmez** (shell env kazanır)."""
    monkeypatch.setenv("TEST_KEY_D", "shell-value")
    envfile = tmp_path / ".env"
    envfile.write_text("TEST_KEY_D=dotenv-value\n", encoding="utf-8")
    n = _load_dotenv(envfile)
    assert n == 0
    assert os.environ["TEST_KEY_D"] == "shell-value"


def test_022_yorum_ve_bos_satir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`#` yorum ve boş satır atlanır."""
    monkeypatch.delenv("TEST_KEY_E", raising=False)
    envfile = tmp_path / ".env"
    envfile.write_text(
        "# bu bir yorum\n"
        "\n"
        "TEST_KEY_E=deger\n"
        "# başka yorum\n",
        encoding="utf-8",
    )
    n = _load_dotenv(envfile)
    assert n == 1
    assert os.environ["TEST_KEY_E"] == "deger"
    monkeypatch.delenv("TEST_KEY_E", raising=False)


def test_022_atlas_dotenv_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ATLAS_DOTENV` env'i verilirse o yol yüklenir."""
    monkeypatch.delenv("TEST_KEY_F", raising=False)
    envfile = tmp_path / "custom.env"
    envfile.write_text("TEST_KEY_F=custom-value\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_DOTENV", str(envfile))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))

    # CLI çalıştırınca main() içindeki _load_dotenv tetiklenir
    main(["doctor", "--json"])
    assert os.environ["TEST_KEY_F"] == "custom-value"
    monkeypatch.delenv("TEST_KEY_F", raising=False)


def test_022_esittensiz_atlanir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`=` yoksa satır atlanır."""
    monkeypatch.delenv("TEST_KEY_G", raising=False)
    envfile = tmp_path / ".env"
    envfile.write_text(
        "bu satirda esittens yok\n"
        "TEST_KEY_G=ok\n",
        encoding="utf-8",
    )
    n = _load_dotenv(envfile)
    assert n == 1
    assert os.environ["TEST_KEY_G"] == "ok"
    monkeypatch.delenv("TEST_KEY_G", raising=False)

"""SPEC 053 — atlas --version root komutu."""

from __future__ import annotations

import pytest

from atlas_core import __version__ as _pkg_version
from atlas_core.cli import main


def test_053_version_bayragi_paket_versiyonunu_basar(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas --version` → `atlas <version>` ve exit 0 (argparse action='version')."""
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert out.strip() == f"atlas {_pkg_version}"


def test_053_kisa_v_bayragi(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas -V` kısa formu aynı çıktıyı verir."""
    with pytest.raises(SystemExit) as excinfo:
        main(["-V"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert out.strip() == f"atlas {_pkg_version}"


def test_053_version_paket_metadata_ile_es(  ) -> None:
    """`atlas_core.__version__` `pyproject.toml`'daki version ile bit-uyumlu.

    Not: `pyproject.toml` tek dinamik kaynak (paket build eder). Bu test
    __version__ sabitinin oradan drift etmediğini garanti eder.
    """
    from pathlib import Path

    text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version"):
            # `version = "0.4.2"` → `0.4.2`
            pyproject_version = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            assert pyproject_version == _pkg_version
            return
    raise AssertionError("pyproject.toml içinde version alanı bulunamadı")


def test_053_help_icinde_version_gorunur(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas --help` çıktısında `--version` bayrağı listelenir."""
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    assert "--version" in out
    assert "-V" in out

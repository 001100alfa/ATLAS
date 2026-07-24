"""tools/make_portable.py saf mantık testleri (ağ/subprocess yok).

Kapsam: Target arşiv/url üretimi, TARGETS bütünlüğü, --list, başlatıcı/setup
script üretimi (_write_scripts). İndirme/derleme yan etkileri test edilmez.
"""
import sys
from pathlib import Path

import pytest

# tools/ paket değil; import için yola ekle.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import make_portable as mp  # noqa: E402


class TestTarget:
    def test_archive_ve_url(self):
        t = mp.Target("demo", "x86_64-unknown-linux-gnu", ("manylinux2014_x86_64",), "unix")
        assert t.archive == (
            f"cpython-{mp.PY_VERSION}+{mp.PBS_TAG}-x86_64-unknown-linux-gnu-install_only.tar.gz"
        )
        assert t.url == mp.PBS_BASE + t.archive
        assert t.url.startswith("https://github.com/astral-sh/python-build-standalone/")


class TestTargets:
    def test_dort_hedef_ve_alanlar(self):
        assert set(mp.TARGETS) == {
            "windows-x86_64", "linux-x86_64", "macos-aarch64", "macos-x86_64"
        }
        for name, t in mp.TARGETS.items():
            assert t.name == name
            assert t.os in {"windows", "unix"}
            assert t.pip_platforms, f"{name} pip_platforms boş"
            assert t.triple

    def test_windows_platform_etiketi(self):
        assert mp.TARGETS["windows-x86_64"].os == "windows"
        assert mp.TARGETS["windows-x86_64"].pip_platforms == ("win_amd64",)
        assert mp.TARGETS["linux-x86_64"].os == "unix"


class TestCLI:
    def test_list_cikis_sifir(self, capsys):
        assert mp.main(["--list"]) == 0
        out = capsys.readouterr().out
        for name in mp.TARGETS:
            assert name in out


class TestWriteScripts:
    def test_windows_scriptleri(self, tmp_path: Path):
        mp._write_scripts(mp.TARGETS["windows-x86_64"], tmp_path)
        assert (tmp_path / "atlas.cmd").exists()
        assert (tmp_path / "atlas-sections.cmd").exists()
        assert (tmp_path / "setup-portable.cmd").exists()
        assert "atlas_core.cli" in (tmp_path / "atlas.cmd").read_text(encoding="utf-8")
        assert "sections.cli" in (tmp_path / "atlas-sections.cmd").read_text(encoding="utf-8")
        assert "--no-index" in (tmp_path / "setup-portable.cmd").read_text(encoding="utf-8")

    def test_unix_scriptleri_lf_ve_calistirilabilir(self, tmp_path: Path):
        mp._write_scripts(mp.TARGETS["linux-x86_64"], tmp_path)
        for fn in ("atlas", "atlas-sections", "setup-portable.sh"):
            p = tmp_path / fn
            assert p.exists(), f"{fn} üretilmedi"
            raw = p.read_bytes()
            assert b"\r\n" not in raw, f"{fn} CRLF içeriyor (LF olmalı)"
        assert "atlas_core.cli" in (tmp_path / "atlas").read_text(encoding="utf-8")
        assert "--no-index" in (tmp_path / "setup-portable.sh").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", list(mp.TARGETS))
def test_archive_adlari_platform_uyumlu(name: str):
    t = mp.TARGETS[name]
    assert t.archive.endswith("-install_only.tar.gz")
    assert t.triple in t.archive

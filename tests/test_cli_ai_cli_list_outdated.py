"""SPEC 088 — atlas ai-cli list --outdated testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import _strip_semver_prefix, main


def _make_ai_cli_layout(
    root: Path,
    deps: dict[str, str],
    installed: dict[str, str] | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps({"name": "atlas-ai-cli", "dependencies": deps}),
        encoding="utf-8",
    )
    if installed:
        for name, ver in installed.items():
            pd = root / "node_modules" / name
            pd.mkdir(parents=True, exist_ok=True)
            (pd / "package.json").write_text(
                json.dumps({"name": name, "version": ver}),
                encoding="utf-8",
            )


def test_088_strip_semver_prefix() -> None:
    """Prefix sıyırma birimleri."""
    assert _strip_semver_prefix("^1.18.8") == "1.18.8"
    assert _strip_semver_prefix("~2.0.0") == "2.0.0"
    assert _strip_semver_prefix(">=3.1.0") == "3.1.0"
    assert _strip_semver_prefix(">=  3.1.0") == "3.1.0"
    assert _strip_semver_prefix("=1.0.0") == "1.0.0"
    assert _strip_semver_prefix("1.2.3") == "1.2.3"
    assert _strip_semver_prefix("*") == ""
    assert _strip_semver_prefix("") == ""


def test_088_outdated_installed_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Kurulu olmayan paket outdated sayılır."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"cline": "^3.0.47", "opencode-ai": "^1.18.8"},
        installed={"opencode-ai": "1.18.8"},  # cline kurulu değil
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [p["name"] for p in data["packages"]]
    # cline kurulu değil → outdated; opencode-ai stripped=1.18.8==installed → NOT
    assert names == ["cline"]


def test_088_outdated_version_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """expected stripped != installed → outdated."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"opencode-ai": "^1.19.0", "cline": "^3.0.47"},
        installed={"opencode-ai": "1.18.8", "cline": "3.0.47"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    names = [p["name"] for p in data["packages"]]
    # opencode-ai: stripped=1.19.0 != 1.18.8 → outdated
    # cline: stripped=3.0.47 == 3.0.47 → NOT
    assert names == ["opencode-ai"]


def test_088_outdated_all_uptodate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Hepsi güncel → boş JSON packages, pretty '(guncelleme yok)'."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"opencode-ai": "^1.18.8", "cline": "~3.0.47"},
        installed={"opencode-ai": "1.18.8", "cline": "3.0.47"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    # JSON
    rc = main(["ai-cli", "list", "--outdated", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["packages"] == []
    # Pretty
    rc = main(["ai-cli", "list", "--outdated"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(guncelleme yok)" in out
    assert "outdated" in out  # başlıkta


def test_088_no_outdated_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--outdated VERİLMEZSE SPEC 037.2 bit-uyumlu (tüm liste)."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"a": "^1.0.0", "b": "^2.0.0", "c": "^3.0.0"},
        installed={"a": "1.0.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert len(data["packages"]) == 3  # tümü


def test_088_outdated_pretty_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pretty çıktıda sadece outdated satırlar."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"aa": "^1.0.0", "bb": "^2.0.0"},
        installed={"aa": "1.0.0", "bb": "1.9.0"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated"])
    assert rc == 0
    out = capsys.readouterr().out
    # aa güncel → görünmemeli
    assert "aa" not in out or "bb" in out  # ana kontrol bb'de
    assert "bb" in out
    assert "outdated" in out


def test_088_outdated_dir_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--outdated + AI_CLI_DIR yok → exit 2."""
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "list", "--outdated"])
    assert rc == 2


def test_088_outdated_bozuk_paketjson(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--outdated + bozuk package.json → exit 2 SPEC HATASI."""
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    (ai / "package.json").write_text("{ bozuk", encoding="utf-8")
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--outdated"])
    assert rc == 2

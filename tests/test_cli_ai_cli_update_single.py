"""SPEC 050 — atlas ai-cli update <name> tek paket güncelleme."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import main


def _mkpkg(root: Path, deps: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps({"dependencies": deps}), encoding="utf-8",
    )


def test_050_run_npm_update_package_argv_iceriyor() -> None:
    """`_run_npm_update` package verilirse argv sonuna eklenir."""
    # Direkt fonksiyonu test edemeyiz (npm çalıştırır), ama argv oluşumunu
    # subprocess.run monkey ile doğrulayalım.
    import atlas_core.cli as _cli
    from atlas_core.cli import _run_npm_update as _run

    captured: dict[str, list[str]] = {}

    class _Fake:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
        captured["argv"] = list(argv)
        return _Fake()

    orig = _cli.subprocess.run  # type: ignore[attr-defined]
    _cli.subprocess.run = fake_run  # type: ignore[attr-defined]
    try:
        _run("/fake/npm", dry_run=False, package="cline")
        assert captured["argv"] == ["/fake/npm", "update", "cline"]
        _run("/fake/npm", dry_run=True, package="cline")
        assert captured["argv"] == ["/fake/npm", "outdated", "--long", "cline"]
        _run("/fake/npm", dry_run=False, package=None)
        assert captured["argv"] == ["/fake/npm", "update"]
    finally:
        _cli.subprocess.run = orig  # type: ignore[attr-defined]


def test_050_cli_tek_paket_dependencies_de_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas ai-cli update kimi` (kimi deps'te yok) → exit 2 SPEC HATASI."""
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"opencode-ai": "^1.18.11", "cline": "^3.0.48"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)

    rc = main(["ai-cli", "update", "kimi"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "kimi" in err
    assert "atlas ai-cli list" in err


def test_050_cli_tek_paket_dependencies_de_var_calisir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas ai-cli update cline` deps'te var → npm update cline çağrılır."""
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"opencode-ai": "^1.18.11", "cline": "^3.0.48"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "portable"))

    calls: list[tuple[str, bool, str | None]] = []

    def fake_run(
        npm_bin: str, dry_run: bool, package: str | None = None,
    ) -> tuple[int, str, str]:
        calls.append((npm_bin, dry_run, package))
        return 0, "updated cline\n", ""

    monkeypatch.setattr(cli_mod, "_run_npm_update", fake_run)
    rc = main(["ai-cli", "update", "cline"])
    assert rc == 0
    assert calls == [("/fake/npm", False, "cline")]
    out = capsys.readouterr().out
    assert "npm update (cline)" in out  # scope label
    assert "updated cline" in out


def test_050_cli_tek_paket_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`update cline --dry-run` → npm outdated cline; exit 0."""
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"cline": "^3.0.48"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "path"))
    monkeypatch.setattr(
        cli_mod, "_run_npm_update",
        lambda _b, _d, package=None: (1, f"outdated {package}\n", ""),
    )

    rc = main(["ai-cli", "update", "cline", "--dry-run"])
    assert rc == 0  # dry-run npm exit yansıtılmaz
    out = capsys.readouterr().out
    assert "npm outdated (cline)" in out
    assert "outdated cline" in out


def test_050_cli_argsiz_hepsini_gunceller_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas ai-cli update` (name yok) → hepsini günceller (SPEC 037.1 bit)."""
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"opencode-ai": "^1.18.11"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "portable"))

    calls: list[str | None] = []

    def fake_run(
        _b: str, _d: bool, package: str | None = None,
    ) -> tuple[int, str, str]:
        calls.append(package)
        return 0, "hepsi guncellendi\n", ""

    monkeypatch.setattr(cli_mod, "_run_npm_update", fake_run)
    rc = main(["ai-cli", "update"])
    assert rc == 0
    assert calls == [None]  # package YOK
    out = capsys.readouterr().out
    # Scope label (paket adı) YOK; source label (portable/path) var:
    # `[ai-cli] npm update (portable: /fake/npm)` bit-uyumlu SPEC 037.1
    assert "npm update (portable: /fake/npm)" in out
    # Emin ol: paket adı parantezi araya girmedi
    assert "npm update (cline" not in out
    assert "npm update (opencode" not in out

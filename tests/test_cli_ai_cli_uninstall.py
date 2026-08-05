"""SPEC 083 — atlas ai-cli uninstall <name> testleri."""

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


def test_083_run_npm_uninstall_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_run_npm_uninstall` argv doğru."""
    import atlas_core.cli as _cli
    captured: dict = {}

    class _Fake:
        returncode = 0
        stdout = "removed 1 package\n"
        stderr = ""

    def fake_run(argv, **kw):
        captured["argv"] = list(argv)
        return _Fake()

    orig = _cli.subprocess.run
    _cli.subprocess.run = fake_run
    try:
        from atlas_core.cli import _run_npm_uninstall
        rc, out, _ = _run_npm_uninstall("/fake/npm", "cline")
        assert rc == 0
        assert "removed 1 package" in out
        assert captured["argv"] == [
            "/fake/npm", "uninstall", "cline", "--save",
        ]
    finally:
        _cli.subprocess.run = orig


def test_083_cli_uninstall_ai_cli_dir_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "uninstall", "cline"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_083_cli_uninstall_deps_de_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"opencode-ai": "^1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "uninstall", "kimi"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "kimi" in err
    assert "atlas ai-cli list" in err


def test_083_cli_uninstall_npm_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"cline": "^3.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: (None, ""))
    rc = main(["ai-cli", "uninstall", "cline"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "npm bulunamadı" in err


def test_083_cli_uninstall_basari(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"cline": "^3.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "portable"))

    calls: list[str] = []

    def fake_uninstall(_b: str, package: str) -> tuple[int, str, str]:
        calls.append(package)
        return 0, f"removed {package}\n", ""

    monkeypatch.setattr(cli_mod, "_run_npm_uninstall", fake_uninstall)
    rc = main(["ai-cli", "uninstall", "cline"])
    assert rc == 0
    assert calls == ["cline"]
    out = capsys.readouterr().out
    assert "npm uninstall (cline)" in out
    assert "removed cline" in out
    assert "kaldırıldı" in out


def test_083_cli_uninstall_npm_hata_yansitilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"cline": "^3.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "path"))
    monkeypatch.setattr(
        cli_mod, "_run_npm_uninstall",
        lambda _b, _p: (1, "", "ENOENT: package broken\n"),
    )
    rc = main(["ai-cli", "uninstall", "cline"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "ENOENT" in err


def test_083_cli_uninstall_subprocess_hata_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"cline": "^3.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "path"))
    monkeypatch.setattr(
        cli_mod, "_run_npm_uninstall",
        lambda _b, _p: (-1, "", "npm çağrısı başarısız"),
    )
    rc = main(["ai-cli", "uninstall", "cline"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "npm çağrısı başarısız" in err

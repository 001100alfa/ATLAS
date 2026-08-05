"""SPEC 060 — atlas ai-cli install <name> testleri."""

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


def test_060_run_npm_install_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_run_npm_install` argv doğru."""
    import atlas_core.cli as _cli
    captured: dict = {}

    class _Fake:
        returncode = 0
        stdout = "added 1 package\n"
        stderr = ""

    def fake_run(argv, **kw):  # type: ignore[no-untyped-def]
        captured["argv"] = list(argv)
        captured["cwd"] = kw.get("cwd")
        return _Fake()

    orig = _cli.subprocess.run
    _cli.subprocess.run = fake_run
    try:
        from atlas_core.cli import _run_npm_install
        rc, out, err = _run_npm_install("/fake/npm", "opencode-ai")
        assert rc == 0
        assert "added 1 package" in out
        assert captured["argv"] == [
            "/fake/npm", "install", "opencode-ai", "--save",
        ]
    finally:
        _cli.subprocess.run = orig


def test_060_cli_install_ai_cli_dir_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "install", "cline"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err


def test_060_cli_install_npm_bulunamadi_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: (None, ""))
    rc = main(["ai-cli", "install", "cline"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "npm bulunamadı" in err


def test_060_cli_install_basari_npm_cagrilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"opencode-ai": "^1.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "portable"))

    calls: list[str] = []

    def fake_install(_b: str, package: str) -> tuple[int, str, str]:
        calls.append(package)
        return 0, f"+ {package}@1.2.3\nadded 1 package\n", ""

    monkeypatch.setattr(cli_mod, "_run_npm_install", fake_install)
    rc = main(["ai-cli", "install", "cline"])
    assert rc == 0
    assert calls == ["cline"]
    out = capsys.readouterr().out
    assert "npm install (cline)" in out
    assert "added 1 package" in out
    assert "atlas ai-cli status cline" in out


def test_060_cli_install_npm_hata_yansitilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """npm exit ≠0 → CLI exit ≠0."""
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "path"))
    monkeypatch.setattr(
        cli_mod, "_run_npm_install",
        lambda _b, _p: (1, "", "ENOENT: package not found\n"),
    )
    rc = main(["ai-cli", "install", "no-such-package"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "ENOENT" in err


def test_060_cli_install_subprocess_hata_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """rc == -1 (OSError) → exit 2 + stderr uyarı."""
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "path"))
    monkeypatch.setattr(
        cli_mod, "_run_npm_install",
        lambda _b, _p: (-1, "", "npm çağrısı başarısız: [Errno 2]"),
    )
    rc = main(["ai-cli", "install", "cline"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "npm çağrısı başarısız" in err


def test_060_cli_install_diger_ai_cli_komutlari_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`atlas ai-cli list` --json ile mevcut davranış (bit-uyumlu)."""
    ai = tmp_path / "ai-cli"
    _mkpkg(ai, {"cline": "^3.0.0"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "packages" in data

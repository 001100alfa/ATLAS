"""SPEC 037.4 — atlas ai-cli status <name> testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import main


def _mkpkg(root: Path, deps: dict[str, str]) -> None:
    """Sahte `tools/ai-cli/package.json` yaz."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        json.dumps({"dependencies": deps}), encoding="utf-8",
    )


def _mkinstalled(root: Path, name: str, version: str, extra_bytes: int = 0) -> None:
    """Sahte `node_modules/<name>/package.json` + isteğe bağlı ek dosya."""
    pkg_dir = root / "node_modules" / name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "package.json").write_text(
        json.dumps({"version": version}), encoding="utf-8",
    )
    if extra_bytes > 0:
        (pkg_dir / "blob.bin").write_bytes(b"x" * extra_bytes)


def _mkbin(root: Path, name: str) -> Path:
    """Sahte `node_modules/.bin/<name>` — Unix çıplak, Windows .cmd."""
    import sys as _sys
    bin_dir = root / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    if _sys.platform == "win32":
        p = bin_dir / f"{name}.cmd"
    else:
        p = bin_dir / name
    p.write_text("#!/bin/sh\necho stub\n", encoding="utf-8")
    return p


def test_037_4_status_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Kurulu paket + up_to_date=True + boyut+bin raporlanır."""
    monkeypatch.chdir(tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"opencode-ai": "^1.18.9"})
    _mkinstalled(tmp_path / "tools/ai-cli", "opencode-ai", "1.18.9",
                 extra_bytes=2048)
    _mkbin(tmp_path / "tools/ai-cli", "opencode")

    rc = main(["ai-cli", "status", "opencode-ai", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["name"] == "opencode-ai"
    assert data["installed_version"] == "1.18.9"
    assert data["declared_version"] == "^1.18.9"
    assert data["up_to_date"] is True
    assert data["size_bytes"] >= 2048  # blob + iki package.json
    assert data["size_human"].endswith(("B", "KB", "MB", "GB"))
    assert data["bin_path"] is None or "opencode" in data["bin_path"]


def test_037_4_status_insan_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"cline": "^3.0.47"})
    _mkinstalled(tmp_path / "tools/ai-cli", "cline", "3.0.47")

    rc = main(["ai-cli", "status", "cline"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "kurulu sürüm:" in out
    assert "3.0.47" in out
    assert "beklenen sürüm:" in out
    assert "^3.0.47" in out
    assert "güncel mi:" in out
    assert "evet" in out


def test_037_4_status_eskimis_up_to_date_hayir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """installed != declared_clean → up_to_date=False, exit 0."""
    monkeypatch.chdir(tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"kilo": "^7.4.17"})
    _mkinstalled(tmp_path / "tools/ai-cli", "kilo", "7.4.16")

    rc = main(["ai-cli", "status", "kilo", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["up_to_date"] is False
    assert data["installed_version"] == "7.4.16"


def test_037_4_status_paket_dependencies_de_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"opencode-ai": "^1.0.0"})

    rc = main(["ai-cli", "status", "kimi"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "kimi" in err
    assert "atlas ai-cli list" in err


def test_037_4_status_kurulu_degil_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """dependencies var ama node_modules/ yok → exit 2."""
    monkeypatch.chdir(tmp_path)
    _mkpkg(tmp_path / "tools/ai-cli", {"kimi": "^2.0.0"})

    rc = main(["ai-cli", "status", "kimi", "--json"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "kurulu değil" in err
    assert "atlas ai-cli update" in err


def test_037_4_status_ai_cli_dir_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    rc = main(["ai-cli", "status", "opencode-ai"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "tools/ai-cli" in err.replace("\\", "/")


def test_037_4_human_bytes_kalibratie(tmp_path: Path) -> None:
    """`_human_bytes`: B → KB → MB eşikleri doğru."""
    from atlas_core.cli import _human_bytes
    assert _human_bytes(0) == "0 B"
    assert _human_bytes(1023) == "1023 B"
    assert _human_bytes(1024).endswith("KB")
    assert _human_bytes(1024 * 1024).endswith("MB")
    assert _human_bytes(1024 * 1024 * 1024).endswith("GB")

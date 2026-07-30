"""SPEC 037 — atlas ai-cli diff-summary testleri."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import (
    _format_bumps,
    _parse_package_lock_diff,
    main,
)

# ─────────────────────────────────────────────────────────────────────
# _parse_package_lock_diff — düz metin parse (subprocess yok)
# ─────────────────────────────────────────────────────────────────────


def test_037_parse_bos_diff() -> None:
    """Boş diff → boş liste."""
    assert _parse_package_lock_diff("") == []


def test_037_parse_tek_paket_bump() -> None:
    """Tek paket bump — (paket, eski, yeni)."""
    diff = """diff --git a/tools/ai-cli/package-lock.json b/tools/ai-cli/package-lock.json
--- a/tools/ai-cli/package-lock.json
+++ b/tools/ai-cli/package-lock.json
@@ -100,7 +100,7 @@
     "node_modules/opencode-ai": {
-      "version": "1.18.8",
+      "version": "1.18.9",
       "resolved": "..."
"""
    bumps = _parse_package_lock_diff(diff)
    assert len(bumps) == 1
    pkg, old, new = bumps[0]
    assert "opencode-ai" in pkg
    assert old == "1.18.8"
    assert new == "1.18.9"


def test_037_parse_coklu_paket_bump() -> None:
    """İki paket bump."""
    diff = """--- a/tools/ai-cli/package-lock.json
+++ b/tools/ai-cli/package-lock.json
     "node_modules/opencode-ai": {
-      "version": "1.18.8",
+      "version": "1.18.9",
     "node_modules/cline": {
-      "version": "3.0.46",
+      "version": "3.0.47",
"""
    bumps = _parse_package_lock_diff(diff)
    assert len(bumps) == 2
    pkgs = {b[0] for b in bumps}
    assert any("opencode-ai" in p for p in pkgs)
    assert any("cline" in p for p in pkgs)


# ─────────────────────────────────────────────────────────────────────
# _format_bumps — commit msg biçimi
# ─────────────────────────────────────────────────────────────────────


def test_037_format_bos() -> None:
    assert _format_bumps([]) == "(diff yok)"


def test_037_format_tek_paket() -> None:
    out = _format_bumps([("opencode-ai", "1.18.8", "1.18.9")])
    assert out == "chore(ai-cli): opencode-ai 1.18.8 → 1.18.9"


def test_037_format_coklu_paket() -> None:
    out = _format_bumps([
        ("opencode-ai", "1.18.8", "1.18.9"),
        ("cline", "3.0.46", "3.0.47"),
    ])
    assert "chore(ai-cli):" in out
    assert "opencode-ai 1.18.8 → 1.18.9" in out
    assert "cline 3.0.46 → 3.0.47" in out
    assert "; " in out


# ─────────────────────────────────────────────────────────────────────
# _cmd_ai_cli_diff_summary — end-to-end (git subprocess mocked)
# ─────────────────────────────────────────────────────────────────────


def test_037_cmd_diff_yok(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Git diff çıktısı boş → `(diff yok)`."""
    monkeypatch.setattr(
        cli_mod, "_run_git_diff_package_lock", lambda: ("", None),
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "(diff yok)"


def test_037_cmd_tek_bump(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Mocked diff → tek bump commit mesajı."""
    fake_diff = (
        '     "node_modules/opencode-ai": {\n'
        '-      "version": "1.18.8",\n'
        '+      "version": "1.18.9",\n'
    )
    monkeypatch.setattr(
        cli_mod, "_run_git_diff_package_lock", lambda: (fake_diff, None),
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out == "chore(ai-cli): opencode-ai 1.18.8 → 1.18.9"


def test_037_cmd_git_yok_failsafe(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Git yoksa (`error` dolu) → fail-safe uyarı + exit 0."""
    monkeypatch.setattr(
        cli_mod, "_run_git_diff_package_lock",
        lambda: ("", "git çağrısı başarısız: FileNotFoundError"),
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("(diff okunamadı:")
    assert "git çağrısı başarısız" in out


def test_037_cmd_dosya_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """`_AI_CLI_PACKAGE_LOCK` yoksa fail-safe (gerçek fonksiyon çağrılır)."""
    monkeypatch.setattr(
        cli_mod, "_AI_CLI_PACKAGE_LOCK", tmp_path / "olmayan-lock.json",
    )
    rc = main(["ai-cli", "diff-summary"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert "dosya yok" in out


# ═════════════════════════════════════════════════════════════════════
# SPEC 037.1 — atlas ai-cli update
# ═════════════════════════════════════════════════════════════════════


def test_0371_ai_cli_dir_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`tools/ai-cli/` yoksa exit 2 + SPEC HATASI."""
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok-ai-cli")
    rc = main(["ai-cli", "update"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "ai-cli" in err


def test_0371_npm_bulunamadi_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AI CLI dir var ama npm hiçbir yerden bulunamıyor → exit 2."""
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: (None, ""))
    rc = main(["ai-cli", "update"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "npm bulunamadı" in err


def test_0371_dry_run_outdated_exit_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--dry-run` → npm outdated çağrılır; npm exit 1 (bulgu var) → exit 0."""
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "portable"))

    calls: list[tuple[str, bool]] = []

    def fake_run(npm_bin: str, dry_run: bool) -> tuple[int, str, str]:
        calls.append((npm_bin, dry_run))
        # npm outdated → paket bulundu → exit 1, ama biz dry-run'da 0 döneriz
        return 1, "opencode-ai  1.18.8  1.18.9\n", ""

    monkeypatch.setattr(cli_mod, "_run_npm_update", fake_run)
    rc = main(["ai-cli", "update", "--dry-run"])
    assert rc == 0  # dry-run → npm exit yansıtılmaz
    out = capsys.readouterr().out
    assert "npm outdated" in out
    assert "opencode-ai" in out
    assert calls == [("/fake/npm", True)]


def test_0371_update_npm_exit_yansitilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`update` (dry-run yok) → npm exit kodu doğrudan dönüş kodu."""
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "path"))
    monkeypatch.setattr(
        cli_mod, "_run_npm_update",
        lambda _b, _d: (0, "changed 3 packages\n", ""),
    )
    rc = main(["ai-cli", "update"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "npm update" in out
    assert "changed 3 packages" in out


def test_0371_run_npm_hatasi_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """subprocess hatası (-1) → exit 2 + stderr uyarı."""
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    monkeypatch.setattr(cli_mod, "_find_npm_bin", lambda: ("/fake/npm", "path"))
    monkeypatch.setattr(
        cli_mod, "_run_npm_update",
        lambda _b, _d: (-1, "", "npm çağrısı başarısız: [Errno 2] ..."),
    )
    rc = main(["ai-cli", "update"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "npm çağrısı başarısız" in err


def test_0371_find_npm_bin_portable_oncelik(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Portable npm varsa system npm'e bakılmaz."""
    import sys as _sys

    from atlas_core.cli import _find_npm_bin

    portable_win = tmp_path / "node" / "npm.cmd"
    portable_unix = tmp_path / "node" / "npm"
    portable_win.parent.mkdir()
    portable_win.write_text("@echo off\n", encoding="utf-8")
    portable_unix.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr(cli_mod, "_PORTABLE_NPM_WIN", portable_win)
    monkeypatch.setattr(cli_mod, "_PORTABLE_NPM_UNIX", portable_unix)

    path, source = _find_npm_bin()
    assert source == "portable"
    assert path is not None
    if _sys.platform == "win32":
        assert path.endswith("npm.cmd")
    else:
        assert path.endswith("npm")


def test_0371_find_npm_bin_bulunamadi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Portable yok + PATH yok → (None, '')."""
    from atlas_core.cli import _find_npm_bin

    monkeypatch.setattr(cli_mod, "_PORTABLE_NPM_WIN", tmp_path / "npm.cmd")
    monkeypatch.setattr(cli_mod, "_PORTABLE_NPM_UNIX", tmp_path / "npm")
    monkeypatch.setattr("shutil.which", lambda _n: None)

    path, source = _find_npm_bin()
    assert path is None
    assert source == ""


# ═════════════════════════════════════════════════════════════════════
# SPEC 037.2 — atlas ai-cli list
# ═════════════════════════════════════════════════════════════════════


def _make_ai_cli_layout(
    root: Path,
    deps: dict[str, str],
    installed: dict[str, str] | None = None,
) -> None:
    """Sahte ai-cli düzeni: package.json + isteğe göre node_modules/<n>."""
    import json as _json

    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        _json.dumps({"name": "atlas-ai-cli", "dependencies": deps}),
        encoding="utf-8",
    )
    if installed:
        for name, ver in installed.items():
            pd = root / "node_modules" / name
            pd.mkdir(parents=True, exist_ok=True)
            (pd / "package.json").write_text(
                _json.dumps({"name": name, "version": ver}),
                encoding="utf-8",
            )


def test_0372_dir_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "list"])
    assert rc == 2
    assert "SPEC HATASI" in capsys.readouterr().err


def test_0372_paket_yok_bos_liste(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """package.json deps boş → 0 paket, exit 0."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(ai, deps={})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(paket yok)" in out


def test_0372_paket_kurulu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """2 paket: biri kurulu, biri değil."""
    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"opencode-ai": "^1.18.8", "cline": "^3.0.47"},
        installed={"opencode-ai": "1.18.9"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "opencode-ai" in out
    assert "1.18.9" in out
    assert "cline" in out
    assert "(kurulu değil)" in out


def test_0372_json_ciktisi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--json` → yapılandırılmış çıktı."""
    import json as _json

    ai = tmp_path / "ai-cli"
    _make_ai_cli_layout(
        ai,
        deps={"opencode-ai": "^1.18.8"},
        installed={"opencode-ai": "1.18.9"},
    )
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list", "--json"])
    assert rc == 0
    data = _json.loads(capsys.readouterr().out.strip())
    assert data["path"] == str(ai)
    assert len(data["packages"]) == 1
    p = data["packages"][0]
    assert p["name"] == "opencode-ai"
    assert p["expected"] == "^1.18.8"
    assert p["installed"] == "1.18.9"


def test_0372_package_json_bozuk_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """package.json bozuk → SPEC HATASI + exit 2."""
    ai = tmp_path / "ai-cli"
    ai.mkdir()
    (ai / "package.json").write_text("{ bozuk json", encoding="utf-8")
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "list"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "package.json" in err
    assert "SPEC HATASI" in err


# ═════════════════════════════════════════════════════════════════════
# SPEC 037.3 — atlas ai-cli exec
# ═════════════════════════════════════════════════════════════════════


def _make_bin_layout(root: Path, bins: dict[str, str]) -> None:
    """`root/node_modules/.bin/` altında shim script'leri oluştur."""
    bin_dir = root / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name, content in bins.items():
        # Windows'ta .cmd, Unix'te çıplak; her ikisini de yaratalım — resolver seçer
        if sys.platform == "win32":
            (bin_dir / f"{name}.cmd").write_text(content, encoding="utf-8")
        else:
            unix = bin_dir / name
            unix.write_text(content, encoding="utf-8")
            import stat as _stat

            unix.chmod(unix.stat().st_mode | _stat.S_IXUSR)


def test_0373_dir_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", tmp_path / "yok")
    rc = main(["ai-cli", "exec", "opencode"])
    assert rc == 2
    assert "SPEC HATASI" in capsys.readouterr().err


def test_0373_bin_yok_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """bin bulunamaz → exit 2 + öneri."""
    ai = tmp_path / "ai-cli"
    (ai / "node_modules" / ".bin").mkdir(parents=True)
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "exec", "yok-boyle"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "yok-boyle" in err
    assert "atlas ai-cli list" in err


def test_0373_resolve_bin_windows_cmd_yolu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Resolver: Windows'ta `.cmd` var → seçer; Unix'te çıplak isim."""
    ai = tmp_path / "ai-cli"
    content = "@echo mock\n" if sys.platform == "win32" else "#!/bin/sh\necho mock\n"
    _make_bin_layout(ai, {"fake": content})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    p = cli_mod._resolve_ai_cli_bin("fake")
    assert p is not None
    if sys.platform == "win32":
        assert p.suffix == ".cmd"
    assert p.is_file()


def test_0373_exec_canli_bin_calisir_exit_yansitir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Sahte bin (exit 0 basar) canlı çalıştırılır; exit doğrudan yansır."""
    ai = tmp_path / "ai-cli"
    if sys.platform == "win32":
        _make_bin_layout(ai, {"fake": "@echo hi\r\n@exit /b 0\r\n"})
    else:
        _make_bin_layout(ai, {"fake": "#!/bin/sh\necho hi\nexit 0\n"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "exec", "fake"])
    assert rc == 0


def test_0373_exec_bin_nonzero_yansitir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Bin exit 7 dönerse CLI exit 7."""
    ai = tmp_path / "ai-cli"
    if sys.platform == "win32":
        _make_bin_layout(ai, {"fake": "@exit /b 7\r\n"})
    else:
        _make_bin_layout(ai, {"fake": "#!/bin/sh\nexit 7\n"})
    monkeypatch.setattr(cli_mod, "_AI_CLI_DIR", ai)
    rc = main(["ai-cli", "exec", "fake"])
    assert rc == 7

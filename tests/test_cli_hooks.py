"""SPEC 034 — atlas hooks install / uninstall / status testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core import cli as cli_mod
from atlas_core.cli import (
    _HOOK_SIGNATURE,
    _is_atlas_hook,
    _resolve_hook_target,
    main,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test için tmp_path'te sahte git repo + izole şablon."""
    # Sahte .git dizini
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    # Sahte şablon
    tmpl = tmp_path / "tools" / "hooks" / "pre-commit"
    tmpl.parent.mkdir(parents=True)
    tmpl.write_text(
        f"#!/usr/bin/env sh\n{_HOOK_SIGNATURE}\nset -e\natlas scan src\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    # cli.py _HOOK_TEMPLATE_PATH göreli Path; chdir sonrası yeni cwd'ye
    # işaret eder. Değişkeni override etmek daha güvenli:
    monkeypatch.setattr(cli_mod, "_HOOK_TEMPLATE_PATH", tmpl)
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))


# ─────────────────────────────────────────────────────────────────────
# _is_atlas_hook + _resolve_hook_target
# ─────────────────────────────────────────────────────────────────────


def test_034_is_atlas_hook_true() -> None:
    """İmza satırı ilk 5 satırda varsa True."""
    text = f"#!/bin/sh\n{_HOOK_SIGNATURE}\nset -e\n"
    assert _is_atlas_hook(text) is True


def test_034_is_atlas_hook_false_yabanci() -> None:
    """İmza yoksa (kullanıcı hook'u) False."""
    text = "#!/bin/sh\necho custom hook\nexit 0\n"
    assert _is_atlas_hook(text) is False


def test_034_resolve_target_repo_yok(tmp_path: Path) -> None:
    """`.git` yoksa None."""
    empty = tmp_path / "empty"
    empty.mkdir()
    assert _resolve_hook_target(cwd=empty) is None


def test_034_resolve_target_repo_var(tmp_path: Path) -> None:
    """`.git` varsa `.git/hooks/pre-commit` döner."""
    (tmp_path / ".git").mkdir(exist_ok=True)
    p = _resolve_hook_target(cwd=tmp_path)
    assert p is not None
    assert p.name == "pre-commit"
    assert p.parent.name == "hooks"


# ─────────────────────────────────────────────────────────────────────
# install
# ─────────────────────────────────────────────────────────────────────


def test_034_install_temiz_repo(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Temiz repo → shim yazılır."""
    rc = main(["hooks", "install"])
    assert rc == 0
    target = tmp_path / ".git" / "hooks" / "pre-commit"
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert _HOOK_SIGNATURE in text
    out = capsys.readouterr().out
    assert "kuruldu" in out


def test_034_install_idempotent_ayni_icerik(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Aynı içerik zaten kurulu → no-op exit 0."""
    main(["hooks", "install"])
    capsys.readouterr()
    rc = main(["hooks", "install"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "güncel" in out or "kuruldu" in out


def test_034_install_yabanci_hook_force_yok_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Yabancı hook + --force yok → SPEC HATASI + exit 2."""
    target = tmp_path / ".git" / "hooks" / "pre-commit"
    target.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    rc = main(["hooks", "install"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "--force" in err
    # Dokunulmamış olmalı
    assert "custom" in target.read_text(encoding="utf-8")


def test_034_install_yabanci_hook_force_yazar(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--force` ile yabancı hook ATLAS shim'iyle değiştirilir."""
    target = tmp_path / ".git" / "hooks" / "pre-commit"
    target.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    rc = main(["hooks", "install", "--force"])
    assert rc == 0
    assert _HOOK_SIGNATURE in target.read_text(encoding="utf-8")


def test_034_install_repo_disi_exit_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """.git yoksa exit 2 SPEC HATASI."""
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    rc = main(["hooks", "install"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert ".git" in err


def test_034_install_sablon_yok_exit_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """Şablon dosyası yoksa exit 2."""
    monkeypatch.setattr(cli_mod, "_HOOK_TEMPLATE_PATH",
                        tmp_path / "olmayan" / "pre-commit")
    rc = main(["hooks", "install"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "SPEC HATASI" in err
    assert "şablon" in err.lower()


# ─────────────────────────────────────────────────────────────────────
# uninstall
# ─────────────────────────────────────────────────────────────────────


def test_034_uninstall_kurulu_siler(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """ATLAS shim'i kuruluysa silinir."""
    main(["hooks", "install"])
    capsys.readouterr()
    target = tmp_path / ".git" / "hooks" / "pre-commit"
    assert target.is_file()
    rc = main(["hooks", "uninstall"])
    assert rc == 0
    assert not target.is_file()


def test_034_uninstall_yok_no_op(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Hook yoksa no-op (idempotent, exit 0)."""
    rc = main(["hooks", "uninstall"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "yok" in out


def test_034_uninstall_yabanci_hook_dokunmaz(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Yabancı hook (imza yok) — dokunulmaz, exit 2."""
    target = tmp_path / ".git" / "hooks" / "pre-commit"
    target.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    rc = main(["hooks", "uninstall"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "imza" in err.lower() or "atlas" in err.lower()
    # Dosya hâlâ orada
    assert target.is_file()
    assert "custom" in target.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────
# status
# ─────────────────────────────────────────────────────────────────────


def test_034_status_kurulu_degil(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kurulu yoksa 'kurulu değil'."""
    rc = main(["hooks", "status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "kurulu değil" in out


def test_034_status_kurulu_guncel(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kurulu + güncel → mesaj gövdesinde 'güncel'."""
    main(["hooks", "install"])
    capsys.readouterr()
    rc = main(["hooks", "status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "güncel" in out


def test_034_status_kurulu_eski(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kurulu ATLAS shim'i ama şablonla farklı → 'UYUŞMUYOR'."""
    target = tmp_path / ".git" / "hooks" / "pre-commit"
    # ATLAS imzalı ama farklı içerik
    target.write_text(
        f"#!/bin/sh\n{_HOOK_SIGNATURE}\nexit 0  # eski\n",
        encoding="utf-8",
    )
    rc = main(["hooks", "status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "UYUŞMUYOR" in out


def test_034_status_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--json` çıktı: alanlar dolu."""
    main(["hooks", "install"])
    capsys.readouterr()
    rc = main(["hooks", "status", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["target_is_atlas"] is True
    assert data["target_up_to_date"] is True
    assert data["template_present"] is True


# ═════════════════════════════════════════════════════════════════════
# SPEC 034.1 — Windows sh.exe guard + shell tespiti
# ═════════════════════════════════════════════════════════════════════


def test_0341_find_shell_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-Windows'ta her zaman `'sh'` döner (POSIX standart)."""
    from atlas_core.cli import _find_hook_shell

    monkeypatch.setattr("sys.platform", "linux")
    assert _find_hook_shell() == "sh"


def test_0341_find_shell_windows_depo_yerel_oncelik(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows'ta depo-yerel `tools/git/usr/bin/sh.exe` PATH'ten önce gelir."""
    from atlas_core.cli import _find_hook_shell

    monkeypatch.setattr("sys.platform", "win32")
    # Sahte depo-yerel sh.exe
    local_sh = tmp_path / "tools" / "git" / "usr" / "bin" / "sh.exe"
    local_sh.parent.mkdir(parents=True)
    local_sh.write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    result = _find_hook_shell()
    assert result is not None
    assert result.endswith("sh.exe")
    # Path resolve edilmiş olmalı; tam eşleşme için normcase
    import os

    assert os.path.normcase(result) == os.path.normcase(str(local_sh.resolve()))


def test_0341_find_shell_windows_bulunamadi(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows + hiçbir shell bulunamıyor → None."""
    from atlas_core.cli import _find_hook_shell

    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.chdir(tmp_path)  # boş dizin; tools/git yok
    # shutil.which mock — hem 'sh' hem 'sh.exe' None
    monkeypatch.setattr("shutil.which", lambda name: None)
    # Klasik Git for Windows dizinlerini de gizle
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    assert _find_hook_shell() is None


def test_0341_install_shell_yok_uyari(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """`hooks install` shell yoksa exit 0 + stderr uyarı."""
    from atlas_core import cli as cli_mod

    monkeypatch.setattr(cli_mod, "_find_hook_shell", lambda: None)
    rc = main(["hooks", "install"])
    assert rc == 0  # install yine başarılı
    captured = capsys.readouterr()
    assert "kuruldu" in captured.out
    assert "sh.exe bulunamadı" in captured.err
    assert "git-bash" in captured.err.lower() or "Git for Windows" in captured.err


def test_0341_install_shell_var_temiz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """`hooks install` shell varsa uyarı YOK (bit-uyumlu 034)."""
    from atlas_core import cli as cli_mod

    monkeypatch.setattr(cli_mod, "_find_hook_shell", lambda: "/usr/bin/sh")
    rc = main(["hooks", "install"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "bulunamadı" not in err


def test_0341_status_shell_alanlari(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """`hooks status --json` shell_available + shell_path alanlarını içerir."""
    from atlas_core import cli as cli_mod

    monkeypatch.setattr(cli_mod, "_find_hook_shell", lambda: "/fake/sh")
    rc = main(["hooks", "status", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["shell_available"] is True
    assert data["shell_path"] == "/fake/sh"


def test_0341_status_shell_yok_insan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """Shell yok + insan format → 'shell: YOK' satırı."""
    from atlas_core import cli as cli_mod

    monkeypatch.setattr(cli_mod, "_find_hook_shell", lambda: None)
    rc = main(["hooks", "status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "shell: YOK" in out

"""SPEC 034.2 — pre-commit shim canlı regresyon testleri.

Amaç: `tools/hooks/pre-commit` şablonunu shell üzerinden ÇALIŞTIR ve
`atlas doctor --strict --scan-src` başarısı/başarısızlığı → shim exit
kodu sözleşmesini doğrula.

Yaklaşım:
- Tmpdir'de mock `atlas` scripti (env `ATLAS_MOCK_EXIT` kadar döner).
- `_find_hook_shell()` ile shell path'i (Windows: sh.exe portable / git-bash).
- Shell yoksa test skip (Windows CI baremetal senaryo).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from atlas_core.cli import _find_hook_shell, _hook_template_text


def _make_mock_atlas(bin_dir: Path) -> Path:
    """Tmpdir'de mock `atlas` scripti oluştur (POSIX sh).

    Env `ATLAS_MOCK_EXIT` (varsayılan 0) → exit kodu.
    Windows'ta sh.exe var olsa da mock POSIX sh script; sh.exe onu çağırır.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "atlas"
    script.write_text(
        "#!/bin/sh\n"
        'echo "mock atlas $*" >&2\n'
        'exit ${ATLAS_MOCK_EXIT:-0}\n',
        encoding="utf-8",
        newline="\n",
    )
    # Unix'te executable bit
    if sys.platform != "win32":
        import stat as _stat

        script.chmod(script.stat().st_mode | _stat.S_IXUSR | _stat.S_IXGRP)
    return script


def _run_hook(shell: str, hook_path: Path, env: dict[str, str]) -> int:
    """Shim'i shell ile çalıştır, exit kodu döner."""
    proc = subprocess.run(  # noqa: S603 - test-yerel argv
        [shell, str(hook_path)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30.0,
    )
    return proc.returncode


@pytest.fixture()
def _hook_env(tmp_path: Path) -> tuple[str, Path, dict[str, str]] | None:
    """Shell bulunamazsa None (test skip); değilse (shell, hook, env)."""
    shell = _find_hook_shell()
    if shell is None:
        return None
    template = _hook_template_text()
    if template is None:
        return None
    hook = tmp_path / "pre-commit"
    hook.write_text(template, encoding="utf-8", newline="\n")
    if sys.platform != "win32":
        import stat as _stat

        hook.chmod(hook.stat().st_mode | _stat.S_IXUSR)

    bin_dir = tmp_path / "bin"
    _make_mock_atlas(bin_dir)
    env = os.environ.copy()
    # PATH başına mock bin ekle → shim `atlas` = mock
    sep = ";" if sys.platform == "win32" else ":"
    env["PATH"] = f"{bin_dir}{sep}{env.get('PATH', '')}"
    return shell, hook, env


def test_0342_hook_calisti_temiz_exit_0(
    _hook_env: tuple[str, Path, dict[str, str]] | None,
) -> None:
    """Mock atlas exit 0 → hook exit 0 (commit izin verilir)."""
    if _hook_env is None:
        pytest.skip("shell veya hook şablonu yok")
    shell, hook, env = _hook_env
    env["ATLAS_MOCK_EXIT"] = "0"
    rc = _run_hook(shell, hook, env)
    assert rc == 0


def test_0342_hook_calisti_sirli_exit_1(
    _hook_env: tuple[str, Path, dict[str, str]] | None,
) -> None:
    """Mock atlas exit 9 (--strict quality warn) → hook exit 1 (commit engellenir)."""
    if _hook_env is None:
        pytest.skip("shell veya hook şablonu yok")
    shell, hook, env = _hook_env
    env["ATLAS_MOCK_EXIT"] = "9"
    rc = _run_hook(shell, hook, env)
    # Shim: `if ! atlas doctor ...; then exit 1; fi` — non-zero mock → exit 1
    assert rc == 1


def test_0342_hook_calisti_scan_bulgu_exit_1(
    _hook_env: tuple[str, Path, dict[str, str]] | None,
) -> None:
    """Mock atlas exit 2 (SPEC HATASI) → hook exit 1 (commit engellenir)."""
    if _hook_env is None:
        pytest.skip("shell veya hook şablonu yok")
    shell, hook, env = _hook_env
    env["ATLAS_MOCK_EXIT"] = "2"
    rc = _run_hook(shell, hook, env)
    assert rc == 1


def test_0342_hook_sablon_atlas_doctor_cagirisi_icerir() -> None:
    """Regresyon: shim şablonu `atlas doctor --strict --scan-src` içerir.

    Shim güncellemesi yanlış komutu çağırırsa canlı hook sessizce boyun
    eğer (exit 0) → sır sızabilir. Bu statik kontrol o regresyona karşı.
    """
    template = _hook_template_text()
    assert template is not None, "hook şablonu bulunamadı"
    assert "atlas doctor --strict --scan-src" in template
    # Fail path: exit 1 + kullanıcıya çözüm önerileri
    assert "commit engellendi" in template
    assert "exit 1" in template

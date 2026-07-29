"""SPEC 002 §3 (FR3) + §5 (FR7) — Action + sandbox jail testleri (Adım 3.2)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from atlas_core.orchestrator.actions import ActionDeniedError, make_action
from atlas_core.orchestrator.goals import Goal


def _goal(
    allowlist: set[str],
    *,
    shell_regex: str | None = None,
    costs: dict[str, float] | None = None,
) -> Goal:
    import re

    return Goal(
        goal="test",
        plan_kind="static",
        plan_steps=(),
        action_allowlist=frozenset(allowlist),
        shell_allow_regex=re.compile(shell_regex) if shell_regex else None,
        judge_kind="file_exists",
        judge_arg="x",
        budget=100.0,
        max_steps=8,
        costs=costs or {"read": 1.0, "write": 2.0, "shell": 5.0},
    )


# --- happy path ---

def test_write_sandbox_icine(tmp_path: Path) -> None:
    act = make_action(_goal({"write"}), tmp_path)
    obs, cost = act("write:hello.txt:merhaba")
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == "merhaba"
    assert cost == 2.0
    assert "yazildi" in obs


def test_read_yazilan_dosyayi_geri_okur(tmp_path: Path) -> None:
    act = make_action(_goal({"read", "write"}), tmp_path)
    act("write:a.txt:icerik")
    obs, cost = act("read:a.txt")
    assert obs == "icerik"
    assert cost == 1.0


def test_shell_izinli_komut_calisir(tmp_path: Path) -> None:
    # platform-nötr: python -c "print(...)"
    exe = sys.executable.replace("\\", "/")
    regex = rf"^{Path(exe).name} -c .*$"
    exit_map: dict[str, int] = {}
    act = make_action(_goal({"shell"}, shell_regex=regex), tmp_path, exit_map)
    obs, cost = act(f"shell:{Path(exe).name} -c \"print('ok')\"")
    assert exit_map["shell"] == 0
    assert "exit=0" in obs
    assert cost == 5.0


# --- deny senaryoları ---

def test_deny_fiil_izinli_degil(tmp_path: Path) -> None:
    act = make_action(_goal({"read"}), tmp_path)
    with pytest.raises(ActionDeniedError, match="fiil izinli değil"):
        act("write:x.txt:pwn")
    assert not (tmp_path / "x.txt").exists()


def test_deny_shell_regex_disi(tmp_path: Path) -> None:
    act = make_action(_goal({"shell"}, shell_regex=r"^echo .*"), tmp_path)
    with pytest.raises(ActionDeniedError, match="shell allowlist"):
        act("shell:rm -rf .")


def test_deny_path_escape_dotdot(tmp_path: Path) -> None:
    act = make_action(_goal({"write"}), tmp_path)
    with pytest.raises(ActionDeniedError, match="sandbox disina"):
        act("write:../escape.txt:pwn")
    assert not (tmp_path.parent / "escape.txt").exists()


@pytest.mark.parametrize(
    "path_arg",
    ["/etc/passwd", "\\pwn.txt"],
)
def test_deny_mutlak_yol(tmp_path: Path, path_arg: str) -> None:
    act = make_action(_goal({"write"}), tmp_path)
    with pytest.raises(ActionDeniedError, match="mutlak yol"):
        act(f"write:{path_arg}:x")


# --- edge ---

def test_gecersiz_plan_bicimi(tmp_path: Path) -> None:
    act = make_action(_goal({"read"}), tmp_path)
    with pytest.raises(ActionDeniedError, match="gecersiz plan"):
        act("readonly")


def test_shell_bilinmeyen_komut(tmp_path: Path) -> None:
    act = make_action(_goal({"shell"}, shell_regex=r"^definitely_not_a_command .*"), tmp_path)
    with pytest.raises(ActionDeniedError, match="bulunamadi"):
        act("shell:definitely_not_a_command foo")


# ---------- SPEC 026: sandbox iyileştirme ----------


def test_026_env_scrub_api_key_sizmaz(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shell subprocess'e ANTHROPIC_API_KEY sızmamalı."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-SUPER-SECRET-DONT-LEAK")
    exe = sys.executable.replace("\\", "/")
    regex = rf"^{Path(exe).name} -c .*$"
    act = make_action(_goal({"shell"}, shell_regex=regex), tmp_path)
    obs, _ = act(
        f"shell:{Path(exe).name} -c \""
        "import os; print(os.environ.get('ANTHROPIC_API_KEY', 'YOK'))\""
    )
    # Subprocess'te env yok — output 'YOK' olmalı, sızmamalı
    assert "SUPER-SECRET" not in obs
    assert "YOK" in obs


def test_026_env_scrub_path_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PATH sandbox'a geçer (whitelist)."""
    exe = sys.executable.replace("\\", "/")
    regex = rf"^{Path(exe).name} -c .*$"
    act = make_action(_goal({"shell"}, shell_regex=regex), tmp_path)
    obs, _ = act(
        f"shell:{Path(exe).name} -c \""
        "import os; print('has-path' if os.environ.get('PATH') else 'no-path')\""
    )
    assert "has-path" in obs


def test_026_atlas_sandbox_path_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ATLAS_SANDBOX_PATH env verilirse PATH o olur."""
    monkeypatch.setenv("ATLAS_SANDBOX_PATH", "/custom/only")
    exe = sys.executable.replace("\\", "/")
    regex = rf"^{Path(exe).name} -c .*$"
    act = make_action(_goal({"shell"}, shell_regex=regex), tmp_path)
    obs, _ = act(
        f"shell:{Path(exe).name} -c \""
        "import os; print(os.environ.get('PATH', 'YOK'))\""
    )
    assert "/custom/only" in obs


def test_026_timeout_env_okuma(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ATLAS_SANDBOX_TIMEOUT env okunur (fail-safe parse hatası)."""
    from atlas_core.orchestrator.actions import _read_sandbox_timeout
    monkeypatch.delenv("ATLAS_SANDBOX_TIMEOUT", raising=False)
    assert _read_sandbox_timeout() == 10.0
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "3.5")
    assert _read_sandbox_timeout() == 3.5
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "abc")
    assert _read_sandbox_timeout() == 10.0
    monkeypatch.setenv("ATLAS_SANDBOX_TIMEOUT", "-1")
    assert _read_sandbox_timeout() == 10.0


def test_026_stderr_observation_da(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """stderr ilk 200 char observation'a `err=<...>` olarak ekleniyor."""
    exe = sys.executable.replace("\\", "/")
    regex = rf"^{Path(exe).name} -c .*$"
    act = make_action(_goal({"shell"}, shell_regex=regex), tmp_path)
    obs, _ = act(
        f"shell:{Path(exe).name} -c \""
        "import sys; sys.stderr.write('bir hata'); print('out')\""
    )
    assert "err=bir hata" in obs
    assert "out=out" in obs


def test_026_scrub_env_whitelist(monkeypatch: pytest.MonkeyPatch) -> None:
    """_scrub_env whitelist dışını atlar."""
    from atlas_core.orchestrator.actions import _scrub_env
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = _scrub_env()
    assert "ANTHROPIC_API_KEY" not in env
    assert "PATH" in env
    assert env["PATH"] == "/usr/bin"

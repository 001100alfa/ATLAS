"""Action fabrikaları — sandbox'a hapsedilmiş read/write/shell.

SPEC 002 §3 (FR3), §5 (FR7). Bu modül `Goal` + `sandbox` alır,
`run_loop`'un beklediği `Action = Callable[[str], tuple[str, float]]`
sözleşmesini karşılayan bir closure döner.

Güvenlik ilkeleri:
- `shell=False` **sabit** — kabuk açılmaz, argümanlar `shlex.split`
  ile ayrılır.
- Sandbox jail: her path `Path.resolve()` ile normalize edilir ve
  sandbox'a **relative** olmak zorundadır (`is_relative_to`).
- Symlink reddedilir (`lstat().st_mode` symlink bit'i) — Linux CI
  güvencesi.
- Bilinmeyen fiil / izin dışı fiil / regex-dışı shell = `ActionDeniedError`.
"""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from pathlib import Path
from stat import S_ISLNK

from atlas_core.orchestrator.goals import Goal

Action = Callable[[str], tuple[str, float]]

SHELL_TIMEOUT_S: float = 10.0


class ActionDeniedError(RuntimeError):
    """İzin ihlali: fiil/kabuk-regex/path kaçışı."""


def _jail(sandbox: Path, user_path: str) -> Path:
    """Kullanıcı path'ini sandbox'a hapsedip mutlak Path döner.

    Raises:
        ActionDeniedError: mutlak yol / `..` kaçışı / symlink.
    """
    # Platform-bagimsiz mutlak-yol reddi: `/`, `\`, `X:` prefixi veya
    # Path.is_absolute() (Windows'ta `/etc/x` False donduğu için manuel kontrol şart).
    if (
        not user_path
        or user_path.startswith(("/", "\\"))
        or (len(user_path) >= 2 and user_path[1] == ":")
        or Path(user_path).is_absolute()
    ):
        raise ActionDeniedError(f"mutlak yol yasak: {user_path!r}")
    p = Path(user_path)
    candidate = (sandbox / p).resolve()
    sandbox_abs = sandbox.resolve()
    if not candidate.is_relative_to(sandbox_abs):
        raise ActionDeniedError(f"sandbox disina cikis: {user_path!r}")
    # Symlink kontrolü: hedef veya ara herhangi bir bileşen link ise reddet.
    cur = candidate
    while cur != sandbox_abs and cur != cur.parent:
        if cur.exists() or cur.is_symlink():
            try:
                if S_ISLNK(cur.lstat().st_mode):
                    raise ActionDeniedError(f"symlink yasak: {user_path!r}")
            except FileNotFoundError:
                pass
        cur = cur.parent
    return candidate


def _parse_plan(plan: str) -> tuple[str, list[str]]:
    """`fiil:arg1[:arg2]` biçimini ayrıştırır (en fazla 2 bölme)."""
    if ":" not in plan:
        raise ActionDeniedError(f"gecersiz plan biçimi (fiil: bekleniyor): {plan!r}")
    parts = plan.split(":", 2)
    verb = parts[0].strip()
    args = parts[1:]
    return verb, args


def make_action(
    goal: Goal, sandbox: Path, last_exit: dict[str, int] | None = None
) -> Action:
    """Sandbox'a hapsedilmiş action closure'u üretir.

    `last_exit` mutable sözlük paylaşılır — `judges.py` shell exit
    kodunu buradan okur (`exit_zero` judge için).
    """
    sandbox.mkdir(parents=True, exist_ok=True)
    exit_map = last_exit if last_exit is not None else {}
    allowed = goal.action_allowlist
    regex = goal.shell_allow_regex
    costs = goal.costs

    def _read(args: list[str]) -> str:
        if len(args) != 1:
            raise ActionDeniedError(f"read arg sayisi 1 olmali, gelen: {len(args)}")
        target = _jail(sandbox, args[0])
        if not target.is_file():
            raise ActionDeniedError(f"read: dosya yok: {args[0]!r}")
        return target.read_text(encoding="utf-8")

    def _write(args: list[str]) -> str:
        if len(args) != 2:
            raise ActionDeniedError(f"write arg sayisi 2 olmali, gelen: {len(args)}")
        target = _jail(sandbox, args[0])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args[1], encoding="utf-8")
        return f"yazildi: {args[0]} ({len(args[1])}b)"

    def _shell(args: list[str]) -> str:
        # shell komutu ":" içerebilir — args listesini yeniden birleştir.
        cmd = ":".join(args).strip()
        if regex is None or not regex.fullmatch(cmd):
            raise ActionDeniedError(f"shell allowlist ihlali: {cmd!r}")
        try:
            proc = subprocess.run(  # noqa: S603 - shell=False, arg listesi
                shlex.split(cmd),
                shell=False,
                cwd=sandbox,
                capture_output=True,
                text=True,
                timeout=SHELL_TIMEOUT_S,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            exit_map["shell"] = -1
            raise ActionDeniedError(f"shell timeout ({SHELL_TIMEOUT_S}s): {cmd!r}") from exc
        except FileNotFoundError as exc:
            exit_map["shell"] = -1
            raise ActionDeniedError(f"shell komutu bulunamadi: {cmd!r}") from exc
        exit_map["shell"] = proc.returncode
        return f"exit={proc.returncode} out={proc.stdout.strip()[:200]}"

    def action(plan: str) -> tuple[str, float]:
        verb, args = _parse_plan(plan)
        if verb not in allowed:
            raise ActionDeniedError(f"fiil izinli değil: {verb!r} (izinli: {sorted(allowed)})")
        if verb == "read":
            obs = _read(args)
        elif verb == "write":
            obs = _write(args)
        elif verb == "shell":
            obs = _shell(args)
        else:  # pragma: no cover - _ALLOWED_VERBS ile ayrı zaten
            raise ActionDeniedError(f"bilinmeyen fiil: {verb!r}")
        return obs, costs.get(verb, 1.0)

    return action

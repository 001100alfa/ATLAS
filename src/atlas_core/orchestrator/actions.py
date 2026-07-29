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

import os
import shlex
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from stat import S_ISLNK

from atlas_core.orchestrator.goals import Goal

# SPEC 026.1: Unix `resource` modülü Windows'ta yok — import guard.
try:
    import resource as _resource  # type: ignore[import-not-found,unused-ignore]
except ImportError:
    _resource = None  # type: ignore[assignment]

Action = Callable[[str], tuple[str, float]]

SHELL_TIMEOUT_S: float = 10.0

# SPEC 026: shell subprocess'e verilecek env whitelist. ATLAS/LLM/API
# key gibi hassas env'ler burada YOK — sandbox'a sızmaz.
_SANDBOX_ENV_WHITELIST: frozenset[str] = frozenset({
    "PATH", "HOME", "USER", "USERPROFILE", "USERNAME",
    "TEMP", "TMP", "TMPDIR",
    "LANG", "LC_ALL", "LC_CTYPE",
    "SYSTEMROOT", "COMSPEC", "WINDIR",  # Windows
    "SHELL",  # Unix
})


def _scrub_env() -> dict[str, str]:
    """SPEC 026: sandbox subprocess'i için whitelist env döner.

    - `_SANDBOX_ENV_WHITELIST` içindeki değişkenler `os.environ`'dan geçer.
    - `ATLAS_SANDBOX_PATH` env verildiyse PATH override edilir.
    - Diğerleri (ANTHROPIC_API_KEY vs.) YOK.
    """
    env: dict[str, str] = {}
    for k in _SANDBOX_ENV_WHITELIST:
        v = os.environ.get(k)
        if v is not None:
            env[k] = v
    override_path = os.environ.get("ATLAS_SANDBOX_PATH", "").strip()
    if override_path:
        env["PATH"] = override_path
    return env


def _read_sandbox_timeout() -> float:
    """SPEC 026: `ATLAS_SANDBOX_TIMEOUT` saniye (varsayılan 10.0).

    Parse hatası veya negatif → varsayılan.
    """
    try:
        v = float(os.environ.get("ATLAS_SANDBOX_TIMEOUT", str(SHELL_TIMEOUT_S)))
    except ValueError:
        return SHELL_TIMEOUT_S
    return v if v > 0 else SHELL_TIMEOUT_S


def _read_positive_int_env(name: str) -> int | None:
    """SPEC 026.1: env değerini pozitif int olarak oku; yoksa/parse hatası → None."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if n > 0 else None


def _build_preexec_fn() -> Callable[[], None] | None:
    """SPEC 026.1: Unix'te RLIMIT_CPU + RLIMIT_AS ayarlayan preexec_fn.

    - Windows'ta (`_resource is None` veya `sys.platform == "win32"`)
      HER ZAMAN None döner — `subprocess.run(preexec_fn=...)` Windows'ta
      ValueError verir.
    - Env yoksa (`CPU_S` ve `MEM_MB` her ikisi de None) → None
      (varsayılan davranış, ekstra fork maliyeti yok).
    - Bir tanesi verilirse setrlimit çağıran callable döner.
    """
    if _resource is None or sys.platform == "win32":
        return None
    cpu_s = _read_positive_int_env("ATLAS_SANDBOX_CPU_S")
    mem_mb = _read_positive_int_env("ATLAS_SANDBOX_MEM_MB")
    if cpu_s is None and mem_mb is None:
        return None

    def _apply_limits() -> None:  # pragma: no cover - fork child, coverage görmez
        if cpu_s is not None:
            _resource.setrlimit(_resource.RLIMIT_CPU, (cpu_s, cpu_s))
        if mem_mb is not None:
            mem_bytes = mem_mb * 1024 * 1024
            _resource.setrlimit(_resource.RLIMIT_AS, (mem_bytes, mem_bytes))

    return _apply_limits


# ─────────────────────────────────────────────────────────────────────
# SPEC 026.2: Windows Job Objects
# ─────────────────────────────────────────────────────────────────────

# Windows API sabitleri
_JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JobObjectExtendedLimitInformation = 9
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001


def _has_windows_sandbox_env() -> bool:
    """SPEC 026.2: MEM_MB veya MAX_PROC env verildi mi."""
    return (
        _read_positive_int_env("ATLAS_SANDBOX_MEM_MB") is not None
        or _read_positive_int_env("ATLAS_SANDBOX_MAX_PROC") is not None
    )


def _apply_windows_job(pid: int, mem_mb: int | None, max_proc: int | None) -> bool:
    """SPEC 026.2: pid'yi bir Job Object'a atar ve limit uygular.

    Yalnız Windows'ta çağrılmalı — non-Windows'ta anında False döner.
    Başarı → True; başarısızlık → stderr uyarı + False (subprocess devam
    eder, ekstra hata değil).

    NOT: `subprocess.Popen` process'i başlatıp pid verir; Job Object
    hemen sonra atanır. Kısa bir race window var ama Python startup
    yükleme dakikalar sürecek bir alloc yapmaz — pratikte yeter.
    """
    if sys.platform != "win32":
        return False
    if mem_mb is None and max_proc is None:
        return False

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # Windows SDK struct isimleri — CapWords ihlali kasıtlı (upstream API).
    class _IO_COUNTERS(ctypes.Structure):  # noqa: N801
        _fields_ = [  # noqa: RUF012
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):  # noqa: N801
        _fields_ = [  # noqa: RUF012
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),  # ULONG_PTR
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):  # noqa: N801
        _fields_ = [  # noqa: RUF012
            ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    # CreateJobObjectW(lpJobAttributes=NULL, lpName=NULL)
    kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        err = ctypes.get_last_error()
        print(f"uyarı: 026.2 CreateJobObjectW başarısız (WinError {err})",
              file=sys.stderr)
        return False

    info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    flags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if mem_mb is not None:
        flags |= _JOB_OBJECT_LIMIT_PROCESS_MEMORY
        info.ProcessMemoryLimit = mem_mb * 1024 * 1024
    if max_proc is not None:
        flags |= _JOB_OBJECT_LIMIT_ACTIVE_PROCESS
        info.BasicLimitInformation.ActiveProcessLimit = max_proc
    info.BasicLimitInformation.LimitFlags = flags

    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    ok = kernel32.SetInformationJobObject(
        job, _JobObjectExtendedLimitInformation,
        ctypes.byref(info), ctypes.sizeof(info),
    )
    if not ok:
        err = ctypes.get_last_error()
        print(f"uyarı: 026.2 SetInformationJobObject başarısız (WinError {err})",
              file=sys.stderr)
        kernel32.CloseHandle(job)
        return False

    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD, wintypes.BOOL, wintypes.DWORD,
    ]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    proc_handle = kernel32.OpenProcess(
        _PROCESS_SET_QUOTA | _PROCESS_TERMINATE, False, pid,
    )
    if not proc_handle:
        err = ctypes.get_last_error()
        print(f"uyarı: 026.2 OpenProcess(pid={pid}) başarısız (WinError {err})",
              file=sys.stderr)
        kernel32.CloseHandle(job)
        return False

    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    ok = kernel32.AssignProcessToJobObject(job, proc_handle)
    if not ok:
        err = ctypes.get_last_error()
        print(f"uyarı: 026.2 AssignProcessToJobObject başarısız (WinError {err})",
              file=sys.stderr)
        kernel32.CloseHandle(proc_handle)
        kernel32.CloseHandle(job)
        return False

    kernel32.CloseHandle(proc_handle)
    # NOT: job handle bilerek KAPATILMIYOR — parent process ömrü boyunca
    # tutulur; kapatılırsa KILL_ON_JOB_CLOSE ile job child'ları ölür ki
    # bu istenmez (job'ı subprocess.communicate ile bekleyeceğiz).
    # subprocess bitince Python GC handle'ı serbest bırakır; o zaman
    # KILL_ON_JOB_CLOSE devreye girer ve arta kalan child'ları temizler.
    return True


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
        # SPEC 026: whitelist env + configurable timeout.
        # SPEC 026.1: Unix'te opt-in RLIMIT_CPU + RLIMIT_AS; Windows'ta None.
        # SPEC 026.2: Windows'ta env varsa Popen + Job Object yolu.
        env = _scrub_env()
        timeout_s = _read_sandbox_timeout()
        preexec = _build_preexec_fn()
        use_win_job = sys.platform == "win32" and _has_windows_sandbox_env()

        try:
            if use_win_job:
                mem_mb = _read_positive_int_env("ATLAS_SANDBOX_MEM_MB")
                max_proc = _read_positive_int_env("ATLAS_SANDBOX_MAX_PROC")
                popen = subprocess.Popen(  # noqa: S603 - shell=False, arg listesi
                    shlex.split(cmd),
                    shell=False,
                    cwd=sandbox,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )
                # Process başlar başlamaz Job Object'a ata. Hata durumunda
                # subprocess yine yürür (fail-safe).
                _apply_windows_job(popen.pid, mem_mb, max_proc)
                try:
                    out_txt, err_txt = popen.communicate(timeout=timeout_s)
                except subprocess.TimeoutExpired as exc:
                    popen.kill()
                    exit_map["shell"] = -1
                    raise ActionDeniedError(
                        f"shell timeout ({timeout_s}s): {cmd!r}"
                    ) from exc
                returncode = popen.returncode
            else:
                proc = subprocess.run(  # noqa: S603 - shell=False, arg listesi
                    shlex.split(cmd),
                    shell=False,
                    cwd=sandbox,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    preexec_fn=preexec,
                )
                out_txt = proc.stdout
                err_txt = proc.stderr
                returncode = proc.returncode
        except subprocess.TimeoutExpired as exc:
            exit_map["shell"] = -1
            raise ActionDeniedError(
                f"shell timeout ({timeout_s}s): {cmd!r}"
            ) from exc
        except FileNotFoundError as exc:
            exit_map["shell"] = -1
            raise ActionDeniedError(f"shell komutu bulunamadi: {cmd!r}") from exc
        exit_map["shell"] = returncode
        # SPEC 026 M4: stdout + stderr birleşik observation.
        out = (out_txt or "").strip()[:200]
        err = (err_txt or "").strip()[:200]
        if err:
            return f"exit={returncode} out={out} err={err}"
        return f"exit={returncode} out={out}"

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

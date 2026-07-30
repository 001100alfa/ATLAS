"""Planner fabrikaları — static (deterministik) + llm (stub|claude|anthropic|acp).

SPEC 002 §3 (FR2). `run_loop`'un beklediği plan sözleşmesi:
`Callable[[goal: str, history: list[tuple[StepKind, str]]], str]`.

SPEC 003 + 003.1 (LLM planner):
- `ATLAS_LLM=stub` (varsayılan): mevcut `plan[stub]:noop` — bit-uyumlu.
- `ATLAS_LLM=claude`: `claude --print` subprocess'iyle her tur planı
  LLM'den alır; `shell=False`, UTF-8 sabit, timeout'lu (Windows tuzağı
  DECISIONS 2026-07-24).
- `ATLAS_LLM=anthropic`: Anthropic Messages API'sine stdlib `urllib`
  ile HTTPS POST (SPEC 003.1). `ANTHROPIC_API_KEY` zorunlu.
- `ATLAS_LLM=acp`: `ATLAS_LLM_ACP_BIN` ile başlatılan subprocess'a
  Agent Client Protocol (ACP) alt kümesi üzerinden text prompt
  (SPEC 003.1). Görev başına tek-oturum, kalıcı bağlantı yok.
- `ATLAS_LLM=<bilinmeyen>`: `NotImplementedError` (mesaj desteklenen
  backend'leri listeler).

Sözleşme değişmezliği: `Planner`, `make_planner`, `PlannerExhaustedError`,
`LLMPlannerError` imzaları korunur; yeni yalnız iç yardımcılar.
"""

from __future__ import annotations

import json
import os
import random
import shlex
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import IO, Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal

# ─────────────────────────────────────────────────────────────────────
# SPEC 039: LLM inflight sayaç (paralel çağrılar için thread-safe)
# ─────────────────────────────────────────────────────────────────────

_INFLIGHT_COUNT: int = 0
_INFLIGHT_LOCK = threading.Lock()


def _inflight_begin() -> int:
    """SPEC 039: LLM çağrısı başlarken sayacı artır, o anki değeri döndür.

    Snapshot bu çağrıyı DAHİL — yani aynı zamanda 2 çağrı varsa 2 döner.
    """
    global _INFLIGHT_COUNT
    with _INFLIGHT_LOCK:
        _INFLIGHT_COUNT += 1
        return _INFLIGHT_COUNT


def _inflight_end() -> None:
    """SPEC 039: LLM çağrısı biterken sayacı azalt (hata olsa bile)."""
    global _INFLIGHT_COUNT
    with _INFLIGHT_LOCK:
        _INFLIGHT_COUNT = max(0, _INFLIGHT_COUNT - 1)


def _inflight_snapshot() -> int:
    """SPEC 039: Anlık inflight sayacı (test/introspection için)."""
    with _INFLIGHT_LOCK:
        return _INFLIGHT_COUNT

Planner = Callable[[str, list[tuple[StepKind, str]]], str]

_MAX_HISTORY_OBSERVES = 3
_DEFAULT_OBS_CHARS = 200
_MAX_OBS_CHARS = 2000
_DEFAULT_TIMEOUT_S = 60
_STDERR_TAIL = 200
_BODY_TAIL = 200
_DEFAULT_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
_ANTHROPIC_VERSION = "2023-06-01"
_ANTHROPIC_MAX_TOKENS = 256
# SPEC 015.1: Anthropic prompt caching resmi tarife çarpanları.
# cache_read = %10 tam fiyat; cache_creation = %125 tam fiyat.
_CACHE_READ_MULT = 0.1
_CACHE_WRITE_MULT = 1.25

# SPEC 008: test için monkeypatch-able uyku hook'u (default time.sleep).
_sleep: Callable[[float], None] = time.sleep


class PlannerExhaustedError(RuntimeError):
    """Static plan listesi tükendi ama hedef sağlanmadı."""


class LLMPlannerError(RuntimeError):
    """LLM subprocess başarısız (komut yok, timeout, exit!=0, boş cevap)."""


class RetryAfterError(LLMPlannerError):
    """SPEC 014: sunucu `Retry-After` başlığı verdi (throttle/rate limit).

    `retry_after_s`: sunucunun önerdiği bekleme (saniye). Retry sarmalayıcı
    bu değeri backoff yerine kullanır (kör bekleme yerine sunucu ipucu).
    """

    def __init__(self, message: str, *, retry_after_s: float) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


def make_planner(
    goal: Goal,
    context: str | None = None,
    *,
    on_usage: Callable[[int, int, int, int], None] | None = None,
) -> Planner:
    """Goal.plan_kind + ATLAS_LLM'e göre uygun planner closure'u üretir.

    - `static`: plan_steps'i sırayla döndürür; tükenirse
      `PlannerExhaustedError`. `context` yok sayılır.
    - `llm` + `ATLAS_LLM=stub` (varsayılan): sabit `plan[stub]:noop`.
      `context` yok sayılır.
    - `llm` + `ATLAS_LLM=claude`: `_claude_planner` — subprocess her tur.
      Verilirse `context` prompt'a otomatik eklenir (SPEC 006).
      Bin bulunamazsa **fabrika anında** `LLMPlannerError`.
    - `llm` + diğer: `NotImplementedError("Görev 003.1'de eklenecek")`.
    """
    if goal.plan_kind == "static":
        steps = list(goal.plan_steps)
        idx = {"i": 0}

        def _static(_goal: str, _history: list[tuple[StepKind, str]]) -> str:
            if idx["i"] >= len(steps):
                raise PlannerExhaustedError(f"plan_steps tukendi ({len(steps)} adim)")
            step = steps[idx["i"]]
            idx["i"] += 1
            return step

        return _static

    if goal.plan_kind == "llm":
        backend = os.environ.get("ATLAS_LLM", "stub")
        if backend == "stub":
            def _stub(_goal: str, _history: list[tuple[StepKind, str]]) -> str:
                return "plan[stub]:noop"

            return _stub
        if backend == "claude":
            return _claude_planner(goal, context=context)
        if backend == "anthropic":
            return _anthropic_planner(goal, context=context, on_usage=on_usage)
        if backend == "acp":
            return _acp_planner(goal, context=context)
        raise NotImplementedError(
            f"LLM backend {backend!r} bilinmiyor "
            "(desteklenen: stub, claude, anthropic, acp)"
        )

    raise ValueError(f"bilinmeyen plan_kind: {goal.plan_kind}")


# ---------- LLM (claude subprocess) yardımcıları ----------


def _resolve_claude_bin() -> str:
    """`claude` komutunun mutlak yolunu döner (Windows'ta `.cmd` dahil).

    Öncelik: `ATLAS_LLM_CLAUDE_BIN` env → `shutil.which("claude")`.
    Bulunamazsa `LLMPlannerError` — kullanıcıya tam çözüm cümlesi.
    """
    override = os.environ.get("ATLAS_LLM_CLAUDE_BIN", "").strip()
    if override:
        if not os.path.isfile(override):
            raise LLMPlannerError(
                f"claude bulunamadı: ATLAS_LLM_CLAUDE_BIN={override!r} dosya değil"
            )
        return override
    found = shutil.which("claude")
    if not found:
        raise LLMPlannerError(
            "claude bulunamadı: PATH'e ekleyin veya "
            "ATLAS_LLM_CLAUDE_BIN ile mutlak yolu verin"
        )
    return found


_MAX_CONTEXT_CHARS = 4000  # SPEC 006: prompt şişmesin — üst emniyet


def _read_obs_chars_env() -> int:
    """SPEC 018: `ATLAS_LLM_OBS_CHARS` (varsayılan 200, aralık [1, 2000]).

    Parse hatası veya aralık dışı → varsayılan (fail-safe).
    """
    try:
        n = int(os.environ.get("ATLAS_LLM_OBS_CHARS", str(_DEFAULT_OBS_CHARS)))
    except ValueError:
        return _DEFAULT_OBS_CHARS
    if n <= 0 or n > _MAX_OBS_CHARS:
        return _DEFAULT_OBS_CHARS
    return n


def _read_obs_head_tail_env() -> tuple[int, int]:
    """SPEC 018.1: `ATLAS_LLM_OBS_HEAD` + `ATLAS_LLM_OBS_TAIL` (100/100).

    Parse hatası → (100, 100). Negatif → 0. head+tail=0 → 018 davranışı.
    """
    try:
        h = int(os.environ.get("ATLAS_LLM_OBS_HEAD", "100"))
    except ValueError:
        h = 100
    try:
        t = int(os.environ.get("ATLAS_LLM_OBS_TAIL", "100"))
    except ValueError:
        t = 100
    return max(h, 0), max(t, 0)


def _trim_obs(obs: str, obs_chars: int) -> str:
    """SPEC 018 + 018.1: gözlem kırpma stratejisi.

    - `len(obs) <= obs_chars` → dokunma.
    - head+tail toplamı >= obs_chars → 018 davranışı (`obs[:obs_chars]`).
    - Aksi hâlde: head + `[... N char atlandı ...]` + tail.
    """
    if len(obs) <= obs_chars:
        return obs
    head, tail = _read_obs_head_tail_env()
    if head + tail == 0 or head + tail >= obs_chars:
        # 018 davranışı: kuyruğu at
        return obs[:obs_chars]
    skipped = len(obs) - head - tail
    return f"{obs[:head]}\n[... {skipped} char atlandı ...]\n{obs[-tail:]}"


# ─────────────────────────────────────────────────────────────────────
# SPEC 018.2: LLM ile gözlem özetleme
# ─────────────────────────────────────────────────────────────────────

_TRUTHY_ENV_VALUES: frozenset[str] = frozenset({"1", "true", "yes", "on"})
_OBS_SUMMARIZE_MAX_INPUT = 2000   # özet promptuna giren obs üst sınırı
_OBS_SUMMARIZE_MAX_OUTPUT = 120   # döndürülen özet üst sınırı
# Uyarı deduplication: aynı backend için stderr'e bir kez bas.
_OBS_SUMMARIZE_WARNED: set[str] = set()


def _reset_obs_summarize_warnings() -> None:
    """Test yardımcısı — uyarı setini sıfırla."""
    _OBS_SUMMARIZE_WARNED.clear()


def _read_env_flag(name: str) -> bool:
    """Env değişkeni truthy mi (`1`/`true`/`yes`/`on`, case-insensitive)."""
    return os.environ.get(name, "").strip().lower() in _TRUTHY_ENV_VALUES


def _effective_obs_summarize(goal: Goal) -> bool:
    """SPEC 018.2: goal.obs_summarize VEYA env override."""
    return goal.obs_summarize or _read_env_flag("ATLAS_LLM_OBS_SUMMARIZE")


def _stub_summarize_obs(obs: str) -> str:
    """SPEC 018.2 stub özet — deterministik, LLM çağrısı YOK.

    Aynı input → aynı output. Test ve stub/claude/acp fallback için.
    """
    n_char = len(obs)
    n_line = obs.count("\n") + 1 if obs else 0
    head = obs.strip().splitlines()[0][:40] if obs.strip() else ""
    return f"[özet: {n_char} char, {n_line} satır, baş: {head!r}...]"


def _build_summarize_prompt(obs: str) -> str:
    """SPEC 018.2/018.3 ortak özet promptu (backend-agnostik)."""
    return (
        "Aşağıdaki komut çıktısını Türkçe TEK cümlede, en fazla 120 "
        "karakterde özetle. Hata varsa hataya odaklan.\n\n"
        f"Çıktı:\n{obs[:_OBS_SUMMARIZE_MAX_INPUT]}"
    )


def _finalize_summary_line(text: str, backend_label: str) -> str:
    """SPEC 018.2/018.3 ortak: ilk satır + 120 char kırpma + biçimleme.

    Boş text → `LLMPlannerError` (üst katman fail-safe'e düşer).
    """
    line = text.splitlines()[0].strip() if text else ""
    if not line:
        raise LLMPlannerError(f"{backend_label} boş özet döndürdü")
    if len(line) > _OBS_SUMMARIZE_MAX_OUTPUT:
        line = line[: _OBS_SUMMARIZE_MAX_OUTPUT - 1] + "…"
    return f"[özet: {line}]"


def _summarize_via_anthropic(obs: str, goal: Goal) -> str:
    """SPEC 018.2 real özet — Anthropic Messages API üstünden.

    `_call_anthropic`'i minimal bir prompt ile tekrar kullanır. Yan
    etkileri (metrics.jsonl kaydı, usage trace) korunur — ekstra
    çağrı ekstra token olarak metrik dosyasında görünür.

    Hata → `LLMPlannerError` (üst katman fail-safe'e düşer).
    """
    api_key, url, model, timeout_s = _resolve_anthropic_env(goal)
    text = _call_anthropic(
        api_key=api_key,
        url=url,
        model=model,
        prompt=_build_summarize_prompt(obs),
        timeout_s=timeout_s,
        # System yok, cache yok, stream yok — minimal.
    )
    return _finalize_summary_line(text, "anthropic")


def _summarize_via_claude(obs: str, _goal: Goal) -> str:
    """SPEC 018.3 real özet — `claude --print` subprocess üzerinden.

    `_call_claude`'u minimal özet prompt'u ile tekrar kullanır.
    Ayrı bir process çağrısı — planner ile aynı bin/timeout ortam
    değişkenlerini kullanır (bin fabrika içinde çözülmüş; burada
    özet için de aynı çözümleme yapılır).

    Hata → `LLMPlannerError` (üst katman fail-safe).
    """
    bin_path = _resolve_claude_bin()
    timeout_s = int(os.environ.get("ATLAS_LLM_TIMEOUT", str(_DEFAULT_TIMEOUT_S)))
    text = _call_claude(bin_path, _build_summarize_prompt(obs), timeout_s)
    return _finalize_summary_line(text, "claude")


def _summarize_via_acp(obs: str, _goal: Goal) -> str:
    """SPEC 018.3 real özet — ACP-lite oturumu üzerinden.

    `_call_acp` her çağrıda yeni oturum başlatır (mevcut kalıp);
    özet için ayrı bir Popen açılır ve minimal prompt gönderilir.

    Hata → `LLMPlannerError` (üst katman fail-safe).
    """
    bin_path, extra = _resolve_acp_bin()
    timeout_s = int(os.environ.get("ATLAS_LLM_TIMEOUT", str(_DEFAULT_TIMEOUT_S)))
    text = _call_acp(bin_path, extra, _build_summarize_prompt(obs), timeout_s)
    return _finalize_summary_line(text, "acp")


def _maybe_summarize_or_trim(obs: str, obs_chars: int, goal: Goal) -> str:
    """SPEC 018.2 + 018.3: dispatch — özetle ya da 018.1 kırp.

    - `len(obs) <= obs_chars` → dokunma (ekstra maliyet yok).
    - `_effective_obs_summarize(goal)` False → `_trim_obs`.
    - Backend `anthropic`/`claude`/`acp` → real özet; hata →
      stderr uyarı + `_trim_obs` fallback.
    - Backend `stub` → deterministik stub özet.
    - Backend bilinmeyen → stub özet (fail-safe; make_planner zaten
      NotImplementedError verir).
    """
    if len(obs) <= obs_chars:
        return obs
    if not _effective_obs_summarize(goal):
        return _trim_obs(obs, obs_chars)

    backend = os.environ.get("ATLAS_LLM", "stub")
    # Dispatch tablosu: her real backend için (özetleyici, hata etiketi)
    _real_summarizers: dict[str, Callable[[str, Goal], str]] = {
        "anthropic": _summarize_via_anthropic,
        "claude": _summarize_via_claude,
        "acp": _summarize_via_acp,
    }
    summarizer = _real_summarizers.get(backend)
    if summarizer is not None:
        try:
            return summarizer(obs, goal)
        except LLMPlannerError as exc:
            print(
                f"uyarı: obs_summarize {backend} çağrısı başarısız "
                f"(kırpmaya düşülüyor): {exc}",
                file=sys.stderr,
            )
            return _trim_obs(obs, obs_chars)

    # stub veya bilinmeyen → sessiz stub özet (deterministik).
    return _stub_summarize_obs(obs)


def _format_prompt(
    goal: Goal,
    history: list[tuple[StepKind, str]],
    context: str | None = None,
    *,
    include_system: bool = True,
) -> str:
    """LLM prompt gövdesini üretir.

    Varsayılan (goal.llm_prompt None): kısa sabit şablon (< 800 karakter,
    context ile ≤ 5000) — mevcut SPEC 003 kalıbı.

    Özel (goal.llm_prompt str + include_system=True): kullanıcı promptu
    **başa** eklenir; ATLAS'ın plan sözleşmesi (verbs + biçim + "TEK
    satır" direktifi) aşağıya taşınır (SPEC 003.2 kalıbı).

    `include_system=False` (SPEC 010): anthropic backend gibi API-native
    `system` alanına ayrıca ekleyen çağıranlar için — `goal.llm_prompt`
    burada **atlanır**, gövdede kısıt + görev + context yer alır.

    `context` verilirse "Önceden bilinen bağlam" bloğu eklenir
    (SPEC 006 FR5). None veya boş string → blok eklenmez.
    """
    verbs = ", ".join(sorted(goal.action_allowlist)) or "(hiç)"
    obs = [text for kind, text in history if kind is StepKind.OBSERVE]
    tail = obs[-_MAX_HISTORY_OBSERVES:]
    obs_chars = _read_obs_chars_env()  # SPEC 018: runtime env okuma
    # SPEC 018.1: head+tail keep — uzun stderr'ın sonundaki hata kaybolmaz.
    # SPEC 018.2: opt-in → LLM özet (backend'e göre); kısa obs no-op.
    obs_block = (
        "\n".join(f"- {_maybe_summarize_or_trim(o, obs_chars, goal)}" for o in tail)
        if tail else "(yok)"
    )
    ctx_block = ""
    if context:
        ctx_trimmed = context.strip()[:_MAX_CONTEXT_CHARS]
        if ctx_trimmed:
            ctx_block = f"\nÖnceden bilinen bağlam (GBrain):\n{ctx_trimmed}\n"

    contract_block = (
        f"Sözleşme: TEK SATIRLIK plan komutu üret. İzin verilen fiiller: {verbs}.\n"
        'Biçim: fiil:arg1[:arg2]. Örnek: "write:notes.txt:merhaba" veya '
        '"shell:echo ok".\n\n'
        f"Son <=3 gözlem (varsa):\n{obs_block}\n\n"
        "Sadece plan satırını yaz, başka açıklama YOK."
    )

    if goal.llm_prompt and include_system:
        # Kullanıcı sistem promptu üstte; görev + context + sözleşme altta.
        return (
            f"{goal.llm_prompt}\n\n"
            f"Görev: {goal.goal}\n"
            f"{ctx_block}\n"
            f"{contract_block}"
        )
    # Varsayılan sabit şablon (bit-uyumlu SPEC 003) — llm_prompt yoksa
    # veya include_system=False ise (system alanı ayrıca ekleniyor).
    return (
        "Sen ATLAS'ın planlama alt-ajansısın. Görev:\n"
        f"{goal.goal}\n"
        f"{ctx_block}\n"
        f"{contract_block}"
    )


def _call_claude(
    bin_path: str,
    prompt: str,
    timeout_s: int,
    *,
    system: str | None = None,
) -> str:
    """`claude --print --output-format text [--append-system-prompt <s>]` çağırır.

    SPEC 010.1: `system` verilirse `--append-system-prompt <text>`
    argümanı eklenir — anthropic native `system` alanıyla simetri.

    Windows uyumu: `shell=False`, `text=True`, `encoding="utf-8"`,
    `errors="replace"`, `input=prompt`, `capture_output=True`.
    Hata durumunda `LLMPlannerError` (Türkçe mesaj).
    """
    argv = [bin_path, "--print", "--output-format", "text"]
    if system:
        argv += ["--append-system-prompt", system]
    try:
        proc = subprocess.run(  # noqa: S603 - bin_path resolve edilmiş, shell=False
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise LLMPlannerError(f"claude timeout: {timeout_s}s aşıldı") from exc
    except OSError as exc:
        raise LLMPlannerError(f"claude başlatılamadı: {exc}") from exc

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()[:_STDERR_TAIL]
        raise LLMPlannerError(
            f"claude exit={proc.returncode}: {stderr or '(stderr boş)'}"
        )

    text = (proc.stdout or "").strip()
    if not text:
        raise LLMPlannerError("claude boş plan cevabı döndürdü")
    # LLM çok satırlı yanıt üretebilir — planlayıcı sözleşmesi TEK satır.
    first_line = text.splitlines()[0].strip()
    if not first_line:
        raise LLMPlannerError("claude boş plan cevabı döndürdü (ilk satır boş)")
    return first_line


def _claude_planner(goal: Goal, context: str | None = None) -> Planner:
    """Fabrika: bin'i erken çözer (fail-fast), closure her turda çağırır.

    `context` verilmişse closure'a bind edilir; her plan çağrısında aynı
    context prompt'a eklenir (SPEC 006 — görev başında tek kez hesaplanır).

    SPEC 010.1: `goal.llm_prompt` set edilmişse claude'a
    `--append-system-prompt` argümanı ile geçer; gövde
    `include_system=False` kalıbıyla üretilir (anthropic ile simetri).
    """
    bin_path = _resolve_claude_bin()  # fail-fast
    timeout_s = int(os.environ.get("ATLAS_LLM_TIMEOUT", str(_DEFAULT_TIMEOUT_S)))
    system = goal.llm_prompt or None

    def _claude(_goal: str, history: list[tuple[StepKind, str]]) -> str:
        prompt = _format_prompt(
            goal, history, context=context, include_system=False
        )
        return _call_claude(bin_path, prompt, timeout_s, system=system)

    return _claude


# ---------- LLM (anthropic HTTPS) yardımcıları ----------


def _resolve_anthropic_env(goal: Goal | None = None) -> tuple[str, str, str, int]:
    """`(api_key, url, model, timeout_s)` döner; env eksikse fail-fast.

    Model öncelik zinciri (SPEC 009):
      1. `goal.llm_model` (YAML'dan görev-başına)
      2. `ATLAS_LLM_MODEL` env
      3. `_DEFAULT_ANTHROPIC_MODEL` sabiti

    `ANTHROPIC_API_KEY` boş → `LLMPlannerError` (fabrika anında).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise LLMPlannerError(
            "ANTHROPIC_API_KEY yok: ortam değişkeni set edin "
            "(veya .env dosyasına ekleyip yeniden yükleyin)"
        )
    url = os.environ.get("ATLAS_LLM_ANTHROPIC_URL", _DEFAULT_ANTHROPIC_URL).strip()
    goal_model = (goal.llm_model if goal is not None else None) or ""
    env_model = os.environ.get("ATLAS_LLM_MODEL", "").strip()
    model = (goal_model or env_model or _DEFAULT_ANTHROPIC_MODEL).strip()
    timeout_s = int(os.environ.get("ATLAS_LLM_TIMEOUT", str(_DEFAULT_TIMEOUT_S)))
    return api_key, url, model, timeout_s


def _call_anthropic(
    api_key: str,
    url: str,
    model: str,
    prompt: str,
    timeout_s: int,
    *,
    system: str | list[dict[str, Any]] | None = None,
    on_usage: Callable[[int, int, int, int], None] | None = None,
    stream: bool = False,
) -> str:
    """SPEC 039: `_call_anthropic_inner`'a `try/finally` sarmalı wrapper.

    Amaç: her koşulda (başarı / raise / erken return) `_inflight_end()`
    çağrılsın (sayaç leak etmesin). Wrapper mantığı basit tut, iç mantığı
    değiştirme.
    """
    inflight_at_start = _inflight_begin()
    try:
        return _call_anthropic_inner(
            api_key, url, model, prompt, timeout_s,
            system=system, on_usage=on_usage, stream=stream,
            inflight_at_start=inflight_at_start,
        )
    finally:
        _inflight_end()


def _call_anthropic_inner(
    api_key: str,
    url: str,
    model: str,
    prompt: str,
    timeout_s: int,
    *,
    system: str | list[dict[str, Any]] | None = None,
    on_usage: Callable[[int, int, int, int], None] | None = None,
    stream: bool = False,
    inflight_at_start: int = 0,
) -> str:
    """Anthropic Messages API — HTTPS POST, ilk satır plan döner.

    SPEC 010: `system` verilirse gövdeye üst-düzey `system` alanı
    olarak eklenir (Anthropic API sözleşmesi). None/boş → alan eklenmez.
    SPEC 015: `system` liste tipindeyse (bloklar formatı) doğrudan
    payload'a bind — cache_control taşımaya izin verir.
    SPEC 019: `stream=True` → request'e `"stream": true` eklenir; SSE
    parse ile ilk newline'da kesilir (algılanan gecikme düşer).
    SPEC 039: `inflight_at_start` — dış wrapper'dan gelen inflight
    snapshot; `_write_metric_for_data`'ya iletilir. Wrapper `finally`
    ile sayacı sıfırlar.

    stdlib `urllib` + `json`. Hiçbir kod yolunda `api_key` stderr/log'a
    yazılmaz — yalnız request header'ına girer.
    """
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": _ANTHROPIC_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system
    if stream:
        payload["stream"] = True
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(  # noqa: S310 - url env kontrollü, https zorlanır
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        },
    )
    try:
        if stream:
            first_line, usage_data = _read_anthropic_stream(req, timeout_s)
            # 011 trace + 013 charge + 023 metrics — usage'dan tam veri
            _emit_anthropic_usage_trace(usage_data)
            _write_metric_for_data(usage_data, inflight=inflight_at_start)
            if on_usage is not None:
                _in, _out, _cc, _cr = _extract_usage(usage_data)
                on_usage(_in, _out, _cc, _cr)
            return first_line
        with urllib_request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
            raw = resp.read()
    except urllib_error.HTTPError as exc:
        try:
            body_snip = exc.read().decode("utf-8", errors="replace")[:_BODY_TAIL]
        except Exception:  # noqa: BLE001 - body okunamaması alt hata; ana hata HTTP
            body_snip = "(gövde okunamadı)"
        # SPEC 014: Retry-After başlığı varsa özel istisna
        retry_after = _parse_retry_after(exc)
        base_msg = f"anthropic HTTP {exc.code}: {body_snip or '(gövde boş)'}"
        if retry_after is not None:
            raise RetryAfterError(
                f"{base_msg} (retry_after={retry_after}s)",
                retry_after_s=retry_after,
            ) from exc
        raise LLMPlannerError(base_msg) from exc
    except urllib_error.URLError as exc:
        # `socket.timeout` Py 3.10+ TimeoutError aliası; URLError'a sarılabilir.
        if isinstance(exc.reason, TimeoutError):
            raise LLMPlannerError(
                f"anthropic timeout: {timeout_s}s aşıldı"
            ) from exc
        raise LLMPlannerError(
            f"anthropic başlatılamadı: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        # `urlopen` bazı yollarda çıplak TimeoutError fırlatır (Py 3.10+).
        raise LLMPlannerError(f"anthropic timeout: {timeout_s}s aşıldı") from exc

    text_raw = raw.decode("utf-8", errors="replace")
    try:
        data: Any = json.loads(text_raw)
    except json.JSONDecodeError as exc:
        raise LLMPlannerError(
            f"anthropic geçersiz JSON: {text_raw[:_BODY_TAIL]}"
        ) from exc

    content = data.get("content") if isinstance(data, dict) else None
    if not isinstance(content, list):
        raise LLMPlannerError("anthropic beklenmedik yanıt yapısı (content yok)")
    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            t = block.get("text")
            if isinstance(t, str):
                text_parts.append(t)
    text = "".join(text_parts).strip()
    if not text:
        raise LLMPlannerError("anthropic boş plan cevabı döndürdü")
    first_line = text.splitlines()[0].strip()
    if not first_line:
        raise LLMPlannerError("anthropic boş plan cevabı döndürdü (ilk satır boş)")
    # SPEC 011: report-only token usage trace (yan etki, sözleşme değişmez).
    _emit_anthropic_usage_trace(data)
    # SPEC 023 + 039: metrics.jsonl'a tek satır yaz (yan etki, hata sessiz).
    _write_metric_for_data(data, inflight=inflight_at_start)
    # SPEC 013 + 015.1: opsiyonel callback ile CallBudget.charge_tokens
    # beslenir; cache alanları kwargs ile aktarılır (varsayılan 0).
    if on_usage is not None:
        _in, _out, _cc, _cr = _extract_usage(data)
        try:
            on_usage(_in, _out, _cc, _cr)
        except Exception:
            # Bütçe aşımı vs. burada yakalanmaz — yukarıya raise et
            # (LLMPlannerError değil BudgetExceededError için de).
            raise
    return first_line


def _metrics_path() -> Path:
    """SPEC 023: `.atlas/metrics.jsonl` yolu (env override edilebilir)."""
    override = os.environ.get("ATLAS_METRICS", "").strip()
    if override:
        return Path(override)
    return Path(".atlas/metrics.jsonl")


def _write_metric_for_data(data: Any, inflight: int | None = None) -> None:
    """SPEC 023 + 039: anthropic response usage'ından metrics satırı yaz.

    SPEC 039: `inflight` verilirse kayıta `inflight: int` alanı EKLENİR
    (o çağrı başlarken alınan snapshot). `None` → alan yazılmaz
    (bit-uyumluluk; mevcut testler etkilenmez).

    Hata sessiz — disk dolu / izin yoksa planlama akışı devam eder.
    """
    try:
        from datetime import datetime as _dt
        in_tok, out_tok, cc, cr = _extract_usage(data)
        cost = _fmt_cost(in_tok, out_tok, cc, cr)
        record: dict[str, Any] = {
            "ts": _dt.now().isoformat(timespec="seconds"),
            "in": in_tok,
            "out": out_tok,
            "cache_c": cc,
            "cache_r": cr,
            "cost": cost,
        }
        # SPEC 039: yalnız verildiyse yazılır (opt-in yayım)
        if inflight is not None:
            record["inflight"] = int(inflight)
        p = _metrics_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 - metrik yazımı ana akışı bloklamamalı
        pass


def _extract_usage(data: Any) -> tuple[int, int, int, int]:
    """`usage` alanlarını yakala; yoksa (0, 0, 0, 0).

    Döner: `(input_tokens, output_tokens, cache_creation_input_tokens,
    cache_read_input_tokens)`. SPEC 015.1 — Anthropic prompt caching
    aktifken cache alanları dolu gelir.
    """
    usage = data.get("usage") if isinstance(data, dict) else None
    in_tok = 0
    out_tok = 0
    cache_c = 0
    cache_r = 0
    if isinstance(usage, dict):
        in_raw = usage.get("input_tokens", 0)
        out_raw = usage.get("output_tokens", 0)
        cc_raw = usage.get("cache_creation_input_tokens", 0)
        cr_raw = usage.get("cache_read_input_tokens", 0)
        if isinstance(in_raw, int):
            in_tok = in_raw
        if isinstance(out_raw, int):
            out_tok = out_raw
        if isinstance(cc_raw, int):
            cache_c = cc_raw
        if isinstance(cr_raw, int):
            cache_r = cr_raw
    return in_tok, out_tok, cache_c, cache_r


def _emit_anthropic_usage_trace(data: Any) -> None:
    """`ATLAS_LLM_TRACE=1` açıkken usage bilgisini stderr'a yaz.

    Kapalıysa yalın no-op — çağrı yolunda yan etki yok. SPEC 015.1:
    cache alanları varsa `in=N (cache=W r=R) out=M` formatı.
    """
    if os.environ.get("ATLAS_LLM_TRACE") != "1":
        return
    in_tok, out_tok, cache_c, cache_r = _extract_usage(data)
    cost_txt = _fmt_cost(in_tok, out_tok, cache_c, cache_r)
    cache_part = ""
    if cache_c or cache_r:
        cache_part = f" (cache={cache_c} r={cache_r})"
    print(
        f"[llm] anthropic tokens: in={in_tok}{cache_part} out={out_tok} "
        f"cost≈{cost_txt}",
        file=sys.stderr,
    )


def _read_anthropic_stream(
    req: urllib_request.Request, timeout_s: int
) -> tuple[str, dict[str, Any]]:
    """SPEC 019: SSE stream'i satır satır oku, ilk newline'da kes.

    Döner: `(first_line, usage_data)` — `usage_data` `_extract_usage`
    formatıyla uyumlu `{"usage": {...}}` dict.
    """
    text_parts: list[str] = []
    usage_data: dict[str, Any] = {"usage": {}}
    resp = urllib_request.urlopen(req, timeout=timeout_s)  # noqa: S310
    try:
        current_event = ""
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                current_event = ""
                continue
            if line.startswith("event: "):
                current_event = line[7:]
                continue
            if not line.startswith("data: "):
                continue
            data_json = line[6:]
            try:
                data = json.loads(data_json)
            except json.JSONDecodeError as exc:
                raise LLMPlannerError(
                    f"streaming: geçersiz SSE data: {data_json[:_BODY_TAIL]}"
                ) from exc
            if not isinstance(data, dict):
                continue
            evt_type = data.get("type") or current_event
            if evt_type == "content_block_delta":
                delta = data.get("delta")
                if isinstance(delta, dict) and delta.get("type") == "text_delta":
                    t = delta.get("text")
                    if isinstance(t, str):
                        text_parts.append(t)
                        joined = "".join(text_parts)
                        # İlk newline gelince kes → algılanan gecikme düşer.
                        if "\n" in joined:
                            first_line = joined.splitlines()[0].strip()
                            if first_line:
                                # message_delta gelmeden kapatıyoruz, usage=0
                                return first_line, usage_data
            elif evt_type == "message_delta":
                # message_delta içinde `usage` (output_tokens güncel)
                d = data.get("usage")
                if isinstance(d, dict):
                    usage_data["usage"].update(d)
            elif evt_type == "message_start":
                # message_start içinde message.usage (input_tokens vs.)
                m = data.get("message")
                if isinstance(m, dict):
                    u = m.get("usage")
                    if isinstance(u, dict):
                        usage_data["usage"].update(u)
            elif evt_type == "message_stop":
                break
    finally:
        try:
            resp.close()
        except Exception:  # noqa: BLE001 - teardown; ana hatayı gölgeleme
            pass

    text = "".join(text_parts).strip()
    if not text:
        raise LLMPlannerError("anthropic boş plan cevabı döndürdü (stream)")
    first_line = text.splitlines()[0].strip()
    if not first_line:
        raise LLMPlannerError("anthropic boş plan cevabı döndürdü (stream, ilk satır boş)")
    return first_line, usage_data


def _fmt_cost(
    in_tok: int, out_tok: int, cache_c: int = 0, cache_r: int = 0
) -> str:
    """Fiyat env'i (per million USD) varsa cost, yoksa `?`.

    SPEC 015.1: cache_creation `_CACHE_WRITE_MULT` (%125),
    cache_read `_CACHE_READ_MULT` (%10) çarpanlı hesaplanır.
    Parse hatası → `?` (fail-safe; kullanıcı env'i yanlış yazarsa
    işlemi kırma).
    """
    try:
        price_in = float(os.environ.get("ATLAS_LLM_PRICE_IN", ""))
        price_out = float(os.environ.get("ATLAS_LLM_PRICE_OUT", ""))
    except ValueError:
        return "?"
    cost = (
        in_tok * price_in / 1_000_000
        + cache_c * price_in * _CACHE_WRITE_MULT / 1_000_000
        + cache_r * price_in * _CACHE_READ_MULT / 1_000_000
        + out_tok * price_out / 1_000_000
    )
    return f"${cost:.6f}"


def _anthropic_planner(
    goal: Goal,
    context: str | None = None,
    *,
    on_usage: Callable[[int, int, int, int], None] | None = None,
) -> Planner:
    """Fabrika: env'i erken çözer (fail-fast), closure her turda çağırır.

    SPEC 009: model önceliği `goal.llm_model` > `ATLAS_LLM_MODEL` env >
    varsayılan; `_resolve_anthropic_env(goal)` içinde çözülür.

    SPEC 010: `goal.llm_prompt` set edilmişse Anthropic API'nin `system`
    alanına yazılır; `messages[0].content` yalnız ATLAS'ın plan
    sözleşmesi + görev + context + geçmiş taşır (`include_system=False`).

    SPEC 013: `on_usage` verilirse her başarılı call sonrası
    `(input_tokens, output_tokens)` ile çağrılır — CLI `CallBudget.
    charge_tokens` bind eder.
    """
    api_key, url, model, timeout_s = _resolve_anthropic_env(goal)  # fail-fast
    system: str | list[dict[str, Any]] | None
    if goal.llm_prompt:
        if goal.prompt_cache:
            # SPEC 015: blok formatı + cache_control ephemeral (5 dk).
            system = [
                {
                    "type": "text",
                    "text": goal.llm_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        else:
            system = goal.llm_prompt
    else:
        system = None

    stream = goal.stream

    def _anthropic(_goal: str, history: list[tuple[StepKind, str]]) -> str:
        prompt = _format_prompt(
            goal, history, context=context, include_system=False
        )
        return _call_anthropic(
            api_key, url, model, prompt, timeout_s,
            system=system, on_usage=on_usage, stream=stream,
        )

    return _anthropic


# ---------- LLM (ACP subprocess) yardımcıları ----------


def _resolve_acp_bin() -> tuple[str, list[str]]:
    """`(bin_path, extra_argv)` döner; bin yoksa fail-fast."""
    override = os.environ.get("ATLAS_LLM_ACP_BIN", "").strip()
    if override:
        if not os.path.isfile(override):
            raise LLMPlannerError(
                f"acp agent bin bulunamadı: ATLAS_LLM_ACP_BIN={override!r} dosya değil"
            )
        bin_path = override
    else:
        found = shutil.which("acp-agent")
        if not found:
            raise LLMPlannerError(
                "acp agent bin bulunamadı: PATH'e ekleyin veya "
                "ATLAS_LLM_ACP_BIN ile mutlak yolu verin"
            )
        bin_path = found
    args_raw = os.environ.get("ATLAS_LLM_ACP_ARGS", "").strip()
    extra = shlex.split(args_raw) if args_raw else []
    return bin_path, extra


def _acp_send(stdin: IO[str], obj: dict[str, Any]) -> None:
    """JSON-RPC 2.0 satırı yazar (newline-delimited, LSP değil ACP klasik)."""
    stdin.write(json.dumps(obj) + "\n")
    stdin.flush()


def _acp_readline(stdout: IO[str], deadline: float) -> str:
    """Satır okur; deadline aşılırsa `TimeoutError`."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("acp readline: son tarih aşıldı")
    # Not: subprocess pipe blocking'dir; timeout gerçek anlamda burada
    # üstten uygulanır (Popen kill). readline dönerse veya EOF gelirse
    # kalan zaman kontrol edilir. Test tarafında monkeypatch belirlenimci.
    line = stdout.readline()
    if line == "":
        # EOF — deadline dolmadıysa erken kapanma anlamına gelir
        raise EOFError("acp: subprocess erken kapandı (EOF)")
    return line


def _call_acp(bin_path: str, extra: list[str], prompt: str, timeout_s: int) -> str:
    """ACP-lite oturumu: initialize → session/new → session/prompt.

    Her plan çağrısı için yeni Popen. Süreç sızıntısı yasak (finally kill).
    """
    argv = [bin_path, *extra]
    try:
        proc = subprocess.Popen(  # noqa: S603 - bin resolve edilmiş, shell=False
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        raise LLMPlannerError(f"acp başlatılamadı: {exc}") from exc

    deadline = time.monotonic() + max(timeout_s, 1)
    collected: list[str] = []
    prompt_id = 3

    try:
        assert proc.stdin is not None
        assert proc.stdout is not None
        # 1. initialize
        _acp_send(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": 1, "clientCapabilities": {}},
            },
        )
        init_resp = _acp_expect_response(proc, expected_id=1, deadline=deadline)
        if "error" in init_resp:
            _raise_acp_error(init_resp["error"], phase="initialize")

        # 2. session/new
        _acp_send(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "session/new",
                "params": {"cwd": os.getcwd(), "mcpServers": []},
            },
        )
        sess_resp = _acp_expect_response(proc, expected_id=2, deadline=deadline)
        if "error" in sess_resp:
            _raise_acp_error(sess_resp["error"], phase="session/new")
        session_id = (
            sess_resp.get("result", {}).get("sessionId")
            if isinstance(sess_resp.get("result"), dict)
            else None
        )
        if not isinstance(session_id, str) or not session_id:
            raise LLMPlannerError("acp: session/new yanıtında sessionId yok")

        # 3. session/prompt
        _acp_send(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "id": prompt_id,
                "method": "session/prompt",
                "params": {
                    "sessionId": session_id,
                    "prompt": [{"type": "text", "text": prompt}],
                },
            },
        )

        # 4. notification akışı: agent_message_chunk topla; id=3 gelene kadar oku
        while True:
            try:
                line = _acp_readline(proc.stdout, deadline)
            except TimeoutError as exc:
                raise LLMPlannerError(f"acp timeout: {timeout_s}s aşıldı") from exc
            except EOFError as exc:
                rc = proc.poll()
                stderr_tail = _read_stderr_tail(proc)
                raise LLMPlannerError(
                    f"acp exit={rc}: {stderr_tail or '(stderr boş)'}"
                ) from exc

            try:
                msg = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LLMPlannerError(
                    f"acp geçersiz JSON satır: {line.strip()[:_BODY_TAIL]}"
                ) from exc
            if not isinstance(msg, dict):
                continue

            # SPEC 016.1: request from agent (method + id) — cevap ver.
            if msg.get("method") is not None and msg.get("id") is not None:
                _acp_handle_client_request(proc.stdin, msg)
                continue

            # notification: session/update (method varsa ama id yok)
            if msg.get("method") == "session/update":
                params = msg.get("params")
                if isinstance(params, dict):
                    upd = params.get("update")
                    if isinstance(upd, dict):
                        kind = upd.get("sessionUpdate")
                        # SPEC 016: tool-use şu an desteklenmiyor — açık red.
                        if kind in ("tool_call", "tool_call_update"):
                            tool_call = upd.get("toolCall")
                            tool_name = (
                                tool_call.get("name")
                                if isinstance(tool_call, dict)
                                else None
                            ) or upd.get("title") or "?"
                            raise LLMPlannerError(
                                f"acp: tool-use şu an desteklenmiyor "
                                f"(Görev 016.1+); agent tool_name={tool_name!r} istedi"
                            )
                        if kind == "agent_message_chunk":
                            chunk = upd.get("content")
                            if isinstance(chunk, dict) and chunk.get("type") == "text":
                                t = chunk.get("text")
                                if isinstance(t, str):
                                    collected.append(t)
                                    # SPEC 019.1: ilk newline'da erken çık.
                                    joined = "".join(collected)
                                    if "\n" in joined:
                                        first = joined.splitlines()[0].strip()
                                        if first:
                                            break  # dış while döngüsünden çık
                continue

            # response
            if msg.get("id") == prompt_id:
                if "error" in msg:
                    _raise_acp_error(msg["error"], phase="session/prompt")
                break

            # diğer id yanıtları / bilinmeyen notification → yok say
            continue

    finally:
        _acp_teardown(proc)

    text = "".join(collected).strip()
    if not text:
        raise LLMPlannerError("acp boş plan cevabı döndürdü")
    first_line = text.splitlines()[0].strip()
    if not first_line:
        raise LLMPlannerError("acp boş plan cevabı döndürdü (ilk satır boş)")
    return first_line


# SPEC 016.1: ACP client-provided methods. Read-only fs.read yeter;
# write/shell reddedilir; bilinmeyen -32601 Method not found.
_ACP_READ_METHODS = frozenset({"fs/read_text_file"})
_ACP_WRITE_METHODS = frozenset(
    {
        "fs/write_text_file",
        "terminal/create",
        "terminal/output",
        "terminal/wait_for_exit",
        "terminal/kill",
        "terminal/release",
    }
)


def _acp_handle_client_request(stdin: IO[str], msg: dict[str, Any]) -> None:
    """Agent'ın gönderdiği client-method request'ine JSON-RPC cevap yaz.

    - `fs/read_text_file`: proje kökü altında güvenli okuma.
    - `session/request_permission` (SPEC 016.2): tool tipine göre
      otomatik karar (read → allow_once; write/shell → reject).
    - Yazma/shell: `-32000 not supported`.
    - Diğer: `-32601 Method not found`.
    """
    method = str(msg.get("method"))
    req_id = msg.get("id")
    if method in _ACP_READ_METHODS:
        _acp_send(stdin, _acp_fs_read_response(req_id, msg.get("params", {})))
        return
    if method == "session/request_permission":
        _acp_send(
            stdin, _acp_permission_response(req_id, msg.get("params", {}))
        )
        return
    if method in _ACP_WRITE_METHODS:
        _acp_send(
            stdin,
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": f"acp client method not supported: {method}",
                },
            },
        )
        return
    _acp_send(
        stdin,
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        },
    )


def _acp_permission_response(
    req_id: Any, params: dict[str, Any]
) -> dict[str, Any]:
    """SPEC 016.2 + 016.3: tool tipine göre permission kararı.

    - Read-only tool → `allow_once` seç.
    - Write/shell tool → `reject`.
    - Bilinmeyen → `reject` (savunmalı).

    SPEC 016.3: `ATLAS_ACP_INTERACTIVE=1` env'inde kullanıcıya
    stdin'den y/n sordurur; boş/hata → auto-karara düşer.

    Yanıt formatı:
    `{"outcome":{"outcome":"selected","optionId":"<X>"}}`.
    Verilen `params.options` içinde eşleşen optionId varsa o kullanılır;
    yoksa sabit fallback.
    """
    tool_call = params.get("toolCall") if isinstance(params, dict) else None
    tool_name = ""
    if isinstance(tool_call, dict):
        raw = tool_call.get("name") or tool_call.get("title")
        if isinstance(raw, str):
            tool_name = raw
    if not tool_name:
        raw_title = params.get("title") if isinstance(params, dict) else None
        if isinstance(raw_title, str):
            tool_name = raw_title

    if tool_name in _ACP_READ_METHODS:
        decision = "allow_once"
    else:
        # Write/shell + bilinmeyen → reject (savunmalı varsayılan)
        decision = "reject"

    # SPEC 016.3: interaktif override
    if os.environ.get("ATLAS_ACP_INTERACTIVE") == "1":
        override = _prompt_acp_permission(tool_name, decision)
        if override is not None:
            decision = override

    # `params.options` içinden eşleşen optionId seç, yoksa fallback sabit.
    options = params.get("options") if isinstance(params, dict) else None
    chosen = decision
    if isinstance(options, list):
        # Öncelik: tam eşleşme
        for opt in options:
            if isinstance(opt, dict) and opt.get("optionId") == decision:
                chosen = decision
                break
        else:
            # Read için `allow_always` → `allow_once`; yoksa `reject`
            if decision == "allow_once":
                for opt in options:
                    if isinstance(opt, dict) and opt.get("optionId") in (
                        "allow_always", "allow"
                    ):
                        oid = opt.get("optionId")
                        if isinstance(oid, str):
                            chosen = oid
                            break
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "outcome": {"outcome": "selected", "optionId": chosen},
        },
    }


def _prompt_acp_permission(tool_name: str, default: str) -> str | None:
    """SPEC 016.3: kullanıcıya y/n sordur; boş/hata → None (fallback).

    - `y`, `yes`, `allow_once`, `allow` → `allow_once`
    - `n`, `no`, `reject` → `reject`
    - Boş → None (auto-karar kullanılır)
    - EOF / KeyboardInterrupt / OSError → None
    """
    try:
        prompt_text = (
            f"[acp permission] tool={tool_name!r} default={default}. "
            "Karar? (y/n/boş): "
        )
        sys.stderr.write(prompt_text)
        sys.stderr.flush()
        line = sys.stdin.readline()
    except (EOFError, KeyboardInterrupt, OSError):
        return None
    ans = line.strip().lower()
    if not ans:
        return None
    if ans in ("y", "yes", "allow_once", "allow"):
        return "allow_once"
    if ans in ("n", "no", "reject"):
        return "reject"
    return None  # bilinmeyen cevap → auto-karara düş


def _acp_fs_read_response(
    req_id: Any, params: dict[str, Any]
) -> dict[str, Any]:
    """`fs/read_text_file` JSON-RPC yanıtı.

    - `params.path`: mutlak yol, proje kökü altında olmalı.
    - `params.line` (opsiyonel, 1-tabanlı) + `params.limit` (opsiyonel).
    - Hata → JSON-RPC error obj.
    """
    path_raw = params.get("path")
    if not isinstance(path_raw, str) or not path_raw:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": "invalid params.path"},
        }
    try:
        target = _resolve_project_path(path_raw)
    except ValueError as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"permission denied: {exc}"},
        }
    if not target.is_file():
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"file not found: {path_raw}"},
        }
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"read failed: {exc}"},
        }
    line_raw = params.get("line")
    limit_raw = params.get("limit")
    if isinstance(line_raw, int) and line_raw > 0:
        lines = text.splitlines()
        start = line_raw - 1
        if isinstance(limit_raw, int) and limit_raw > 0:
            lines = lines[start : start + limit_raw]
        else:
            lines = lines[start:]
        text = "\n".join(lines)
    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": text}}


def _resolve_project_path(path_str: str) -> Path:
    """Proje kökü altındaki dosya yolunu güvenli çöz — traversal engelli.

    Kök: `os.getcwd()`. Path kök altında değilse `ValueError`.
    """
    root = Path(os.getcwd()).resolve()
    p = Path(path_str)
    if not p.is_absolute():
        p = root / p
    resolved = p.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"outside project root: {path_str}") from exc
    return resolved


def _acp_expect_response(
    proc: subprocess.Popen[str], expected_id: int, deadline: float
) -> dict[str, Any]:
    """`id == expected_id` olan response gelene kadar okur (bildirimleri yok sayar)."""
    assert proc.stdout is not None
    while True:
        try:
            line = _acp_readline(proc.stdout, deadline)
        except TimeoutError as exc:
            raise LLMPlannerError("acp timeout: yanıt beklenirken") from exc
        except EOFError as exc:
            rc = proc.poll()
            stderr_tail = _read_stderr_tail(proc)
            raise LLMPlannerError(
                f"acp exit={rc}: {stderr_tail or '(stderr boş)'}"
            ) from exc
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LLMPlannerError(
                f"acp geçersiz JSON satır: {line.strip()[:_BODY_TAIL]}"
            ) from exc
        if isinstance(msg, dict) and msg.get("id") == expected_id:
            return msg


def _raise_acp_error(err: Any, *, phase: str) -> None:  # noqa: ANN401
    """JSON-RPC error nesnesinden `LLMPlannerError` üretir."""
    if isinstance(err, dict):
        message = str(err.get("message", "bilinmiyor"))
    else:
        message = str(err)
    raise LLMPlannerError(f"acp error [{phase}]: {message}")


def _read_stderr_tail(proc: subprocess.Popen[str]) -> str:
    if proc.stderr is None:
        return ""
    try:
        rest = proc.stderr.read() or ""
    except Exception:  # noqa: BLE001 - stderr'ı okuyamamak fatal değil
        return ""
    return rest.strip()[:_STDERR_TAIL]


def _acp_teardown(proc: subprocess.Popen[str]) -> None:
    """`finally`: stdin kapa, kısa wait, hâlâ ayaktaysa kill. Sızıntı yasak."""
    try:
        if proc.stdin is not None and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except Exception:  # noqa: BLE001
                pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
    except Exception:  # noqa: BLE001 - teardown asla ana hatayı gölgeleme
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


def _acp_planner(goal: Goal, context: str | None = None) -> Planner:
    """Fabrika: bin'i erken çözer (fail-fast), closure her turda oturum açar."""
    bin_path, extra = _resolve_acp_bin()  # fail-fast
    timeout_s = int(os.environ.get("ATLAS_LLM_TIMEOUT", str(_DEFAULT_TIMEOUT_S)))

    def _acp(_goal: str, history: list[tuple[StepKind, str]]) -> str:
        prompt = _format_prompt(goal, history, context=context)
        return _call_acp(bin_path, extra, prompt, timeout_s)

    return _acp


# ---------- SPEC 008 + 014: retry/backoff/jitter/retry-after ----------


def _read_retry_env() -> tuple[int, float]:
    """`(retries, backoff_s)` — env'den oku, negatifleri 0'a düşür.

    - `ATLAS_LLM_RETRIES` (varsayılan 0 = kapalı).
    - `ATLAS_LLM_BACKOFF` saniye taban (varsayılan 1.0).
    Sayısal parse hatası doğal `ValueError` — kullanıcı env'i düzeltsin.
    """
    retries = int(os.environ.get("ATLAS_LLM_RETRIES", "0"))
    backoff = float(os.environ.get("ATLAS_LLM_BACKOFF", "1.0"))
    return max(0, retries), max(0.0, backoff)


def _read_jitter_env() -> float:
    """SPEC 014: `ATLAS_LLM_JITTER` üst-sınır saniye (varsayılan 0.0).

    Parse hatası veya negatif → 0 (kapalı; deterministik backoff).
    """
    try:
        j = float(os.environ.get("ATLAS_LLM_JITTER", "0"))
    except ValueError:
        return 0.0
    return max(j, 0.0)


def _parse_retry_after(exc: urllib_error.HTTPError) -> float | None:
    """SPEC 014: `Retry-After` başlığından saniye çıkarır.

    Yalnız int saniye kabul edilir (HTTP-Date formatı kapsam DIŞI —
    Anthropic saniye kullanır). Yoksa/parse hatası → None.
    """
    headers = getattr(exc, "headers", None)
    if headers is None:
        return None
    raw = headers.get("Retry-After")
    if raw is None:
        return None
    try:
        val = float(str(raw).strip())
    except ValueError:
        return None
    return val if val >= 0 else None


def make_retrying_planner(
    inner: Planner, retries: int, backoff_s: float
) -> Planner:
    """LLMPlannerError için üstel-backoff'lu retry sarmalayıcı.

    - `retries <= 0` → `inner` aynen döner (kimlik-geçiş, no-op).
    - Aksi hâlde: en fazla `1 + retries` deneme.
    - Bekleme: `backoff * 2**attempt + random.uniform(0, jitter)`.
      `RetryAfterError` (SPEC 014) yakalanırsa bekleme = header saniyesi
      (backoff yerine, jitter ilaveten değil — sunucu ipucuna saygı).
    - Yalnız `LLMPlannerError` (ve alt sınıfı `RetryAfterError`)
      yakalanır — diğer istisnalar sarma geçer.
    - `ATLAS_LLM_TRACE=1` env'inde her başarısız deneme stderr'a yazılır.

    Sözleşme değişmezliği: dönen callable `Planner` tipi
    (`(goal, history) -> str`).
    """
    if retries <= 0:
        return inner
    jitter = _read_jitter_env()

    def _retrying(goal: str, history: list[tuple[StepKind, str]]) -> str:
        total = 1 + retries
        last_exc: LLMPlannerError | None = None
        for attempt in range(total):
            try:
                return inner(goal, history)
            except LLMPlannerError as exc:
                last_exc = exc
                if os.environ.get("ATLAS_LLM_TRACE") == "1":
                    print(
                        f"[retry] deneme {attempt + 1}/{total} başarısız: "
                        f"{str(exc)[:_BODY_TAIL]}",
                        file=sys.stderr,
                    )
                if attempt < retries:
                    if isinstance(exc, RetryAfterError):
                        # Sunucu ipucu: backoff yerine header saniyesi.
                        wait = exc.retry_after_s
                    else:
                        wait = backoff_s * (2 ** attempt)
                        if jitter > 0:
                            wait += random.uniform(0, jitter)
                    _sleep(wait)
        # Buraya asla düşmemeli (yukarıdaki return veya son hata) —
        # emniyet için son hatayı raise.
        assert last_exc is not None
        raise last_exc

    return _retrying

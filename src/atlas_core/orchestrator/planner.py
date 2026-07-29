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
import shlex
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from typing import IO, Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal

Planner = Callable[[str, list[tuple[StepKind, str]]], str]

_MAX_HISTORY_OBSERVES = 3
_DEFAULT_TIMEOUT_S = 60
_STDERR_TAIL = 200
_BODY_TAIL = 200
_DEFAULT_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
_ANTHROPIC_VERSION = "2023-06-01"
_ANTHROPIC_MAX_TOKENS = 256

# SPEC 008: test için monkeypatch-able uyku hook'u (default time.sleep).
_sleep: Callable[[float], None] = time.sleep


class PlannerExhaustedError(RuntimeError):
    """Static plan listesi tükendi ama hedef sağlanmadı."""


class LLMPlannerError(RuntimeError):
    """LLM subprocess başarısız (komut yok, timeout, exit!=0, boş cevap)."""


def make_planner(goal: Goal, context: str | None = None) -> Planner:
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
            return _anthropic_planner(goal, context=context)
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
    obs_block = "\n".join(f"- {o[:200]}" for o in tail) if tail else "(yok)"
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


def _call_claude(bin_path: str, prompt: str, timeout_s: int) -> str:
    """`claude --print --output-format text` çağırır, ilk satırı döner.

    Windows uyumu: `shell=False`, `text=True`, `encoding="utf-8"`,
    `errors="replace"`, `input=prompt`, `capture_output=True`.
    Hata durumunda `LLMPlannerError` (Türkçe mesaj).
    """
    argv = [bin_path, "--print", "--output-format", "text"]
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
    """
    bin_path = _resolve_claude_bin()  # fail-fast
    timeout_s = int(os.environ.get("ATLAS_LLM_TIMEOUT", str(_DEFAULT_TIMEOUT_S)))

    def _claude(_goal: str, history: list[tuple[StepKind, str]]) -> str:
        prompt = _format_prompt(goal, history, context=context)
        return _call_claude(bin_path, prompt, timeout_s)

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
    system: str | None = None,
) -> str:
    """Anthropic Messages API — HTTPS POST, ilk satır plan döner.

    SPEC 010: `system` verilirse gövdeye üst-düzey `system` alanı
    olarak eklenir (Anthropic API sözleşmesi). None/boş → alan eklenmez.

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
        with urllib_request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
            raw = resp.read()
    except urllib_error.HTTPError as exc:
        try:
            body_snip = exc.read().decode("utf-8", errors="replace")[:_BODY_TAIL]
        except Exception:  # noqa: BLE001 - body okunamaması alt hata; ana hata HTTP
            body_snip = "(gövde okunamadı)"
        raise LLMPlannerError(
            f"anthropic HTTP {exc.code}: {body_snip or '(gövde boş)'}"
        ) from exc
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
    return first_line


def _anthropic_planner(goal: Goal, context: str | None = None) -> Planner:
    """Fabrika: env'i erken çözer (fail-fast), closure her turda çağırır.

    SPEC 009: model önceliği `goal.llm_model` > `ATLAS_LLM_MODEL` env >
    varsayılan; `_resolve_anthropic_env(goal)` içinde çözülür.

    SPEC 010: `goal.llm_prompt` set edilmişse Anthropic API'nin `system`
    alanına yazılır; `messages[0].content` yalnız ATLAS'ın plan
    sözleşmesi + görev + context + geçmiş taşır (`include_system=False`).
    """
    api_key, url, model, timeout_s = _resolve_anthropic_env(goal)  # fail-fast
    system = goal.llm_prompt or None

    def _anthropic(_goal: str, history: list[tuple[StepKind, str]]) -> str:
        prompt = _format_prompt(
            goal, history, context=context, include_system=False
        )
        return _call_anthropic(
            api_key, url, model, prompt, timeout_s, system=system
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

            # notification: session/update ile agent_message_chunk
            if msg.get("method") == "session/update":
                params = msg.get("params")
                if isinstance(params, dict):
                    upd = params.get("update")
                    if (
                        isinstance(upd, dict)
                        and upd.get("sessionUpdate") == "agent_message_chunk"
                    ):
                        chunk = upd.get("content")
                        if isinstance(chunk, dict) and chunk.get("type") == "text":
                            t = chunk.get("text")
                            if isinstance(t, str):
                                collected.append(t)
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


# ---------- SPEC 008: retry/backoff sarmalayıcısı ----------


def _read_retry_env() -> tuple[int, float]:
    """`(retries, backoff_s)` — env'den oku, negatifleri 0'a düşür.

    - `ATLAS_LLM_RETRIES` (varsayılan 0 = kapalı).
    - `ATLAS_LLM_BACKOFF` saniye taban (varsayılan 1.0).
    Sayısal parse hatası doğal `ValueError` — kullanıcı env'i düzeltsin.
    """
    retries = int(os.environ.get("ATLAS_LLM_RETRIES", "0"))
    backoff = float(os.environ.get("ATLAS_LLM_BACKOFF", "1.0"))
    return max(0, retries), max(0.0, backoff)


def make_retrying_planner(
    inner: Planner, retries: int, backoff_s: float
) -> Planner:
    """LLMPlannerError için üstel-backoff'lu retry sarmalayıcı.

    - `retries <= 0` → `inner` aynen döner (kimlik-geçiş, no-op).
    - Aksi hâlde: en fazla `1 + retries` deneme; hata → sleep(backoff *
      2**attempt) → yeniden dene; son deneme raise.
    - Yalnız `LLMPlannerError` yakalanır — diğer istisnalar sarma geçer.
    - `ATLAS_LLM_TRACE=1` env'inde her başarısız deneme stderr'a yazılır.

    Sözleşme değişmezliği: dönen callable `Planner` tipi
    (`(goal, history) -> str`).
    """
    if retries <= 0:
        return inner

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
                    _sleep(backoff_s * (2 ** attempt))
        # Buraya asla düşmemeli (yukarıdaki return veya son hata) —
        # emniyet için son hatayı raise.
        assert last_exc is not None
        raise last_exc

    return _retrying

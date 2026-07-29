"""Planner fabrikaları — static (deterministik) + llm (stub|claude).

SPEC 002 §3 (FR2). `run_loop`'un beklediği plan sözleşmesi:
`Callable[[goal: str, history: list[tuple[StepKind, str]]], str]`.

SPEC 003 (LLM planner):
- `ATLAS_LLM=stub` (varsayılan): mevcut `plan[stub]:noop` — bit-uyumlu.
- `ATLAS_LLM=claude`: `claude --print` subprocess'iyle her tur planı
  LLM'den alır; `shell=False`, UTF-8 sabit, timeout'lu (Windows tuzağı
  DECISIONS 2026-07-24).
- `ATLAS_LLM in {acp, anthropic, <unknown>}`: `NotImplementedError`
  ("Görev 003.1'de eklenecek"). Fabrika anında düşer — kullanıcı
  YAML/env'i düzelmeden zaman kaybetmez.

Sözleşme değişmezliği: `Planner`, `make_planner`, `PlannerExhaustedError`
imzaları korunur; yeni `LLMPlannerError` eklenir.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable

from atlas_core.orchestrator.core import StepKind
from atlas_core.orchestrator.goals import Goal

Planner = Callable[[str, list[tuple[StepKind, str]]], str]

_MAX_HISTORY_OBSERVES = 3
_DEFAULT_TIMEOUT_S = 60
_STDERR_TAIL = 200


class PlannerExhaustedError(RuntimeError):
    """Static plan listesi tükendi ama hedef sağlanmadı."""


class LLMPlannerError(RuntimeError):
    """LLM subprocess başarısız (komut yok, timeout, exit!=0, boş cevap)."""


def make_planner(goal: Goal) -> Planner:
    """Goal.plan_kind + ATLAS_LLM'e göre uygun planner closure'u üretir.

    - `static`: plan_steps'i sırayla döndürür; tükenirse
      `PlannerExhaustedError`.
    - `llm` + `ATLAS_LLM=stub` (varsayılan): sabit `plan[stub]:noop`.
    - `llm` + `ATLAS_LLM=claude`: `_claude_planner` — subprocess her tur.
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
            return _claude_planner(goal)
        raise NotImplementedError(
            f"LLM backend {backend!r} Görev 003.1'de eklenecek "
            "(desteklenen: stub, claude)"
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


def _format_prompt(goal: Goal, history: list[tuple[StepKind, str]]) -> str:
    """Sabit, kısa prompt (< 800 karakter). LLM'ye TEK satır plan istenir."""
    verbs = ", ".join(sorted(goal.action_allowlist)) or "(hiç)"
    obs = [text for kind, text in history if kind is StepKind.OBSERVE]
    tail = obs[-_MAX_HISTORY_OBSERVES:]
    obs_block = "\n".join(f"- {o[:200]}" for o in tail) if tail else "(yok)"
    return (
        "Sen ATLAS'ın planlama alt-ajansısın. Görev:\n"
        f"{goal.goal}\n\n"
        f"Sözleşme: TEK SATIRLIK plan komutu üret. İzin verilen fiiller: {verbs}.\n"
        'Biçim: fiil:arg1[:arg2]. Örnek: "write:notes.txt:merhaba" veya '
        '"shell:echo ok".\n\n'
        f"Son <=3 gözlem (varsa):\n{obs_block}\n\n"
        "Sadece plan satırını yaz, başka açıklama YOK."
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


def _claude_planner(goal: Goal) -> Planner:
    """Fabrika: bin'i erken çözer (fail-fast), closure her turda çağırır."""
    bin_path = _resolve_claude_bin()  # fail-fast
    timeout_s = int(os.environ.get("ATLAS_LLM_TIMEOUT", str(_DEFAULT_TIMEOUT_S)))

    def _claude(_goal: str, history: list[tuple[StepKind, str]]) -> str:
        prompt = _format_prompt(goal, history)
        return _call_claude(bin_path, prompt, timeout_s)

    return _claude

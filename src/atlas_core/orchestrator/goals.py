"""Hedef (Goal) yükleyici — YAML tabanlı sözleşme.

SPEC 002 §5. `atlas run --goal-file <path>` bu modülü çağırır.
Yükleme zamanı doğrulaması sıkıdır: geçersiz alan koşuya değil,
kullanıcıya erken hata olarak döner (exit 2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

PlanKind = Literal["static", "llm"]
JudgeKind = Literal["file_exists", "regex_in_last_observe", "exit_zero"]

_ALLOWED_VERBS: frozenset[str] = frozenset({"read", "write", "shell"})
_ALLOWED_PLAN_KINDS: frozenset[str] = frozenset({"static", "llm"})
_ALLOWED_JUDGE_KINDS: frozenset[str] = frozenset(
    {"file_exists", "regex_in_last_observe", "exit_zero"}
)
_DEFAULT_COSTS: dict[str, float] = {"read": 1.0, "write": 2.0, "shell": 5.0}


class SpecError(ValueError):
    """YAML hedef dosyası şema/anlam hatası."""


_MAX_CONTEXT_LIMIT = 50


@dataclass(frozen=True, slots=True)
class Goal:
    """Doğrulanmış hedef sözleşmesi (çalışma zamanı değişmez)."""

    goal: str
    plan_kind: PlanKind
    plan_steps: tuple[str, ...]
    action_allowlist: frozenset[str]
    shell_allow_regex: re.Pattern[str] | None
    judge_kind: JudgeKind
    judge_arg: str
    budget: float
    max_steps: int
    costs: dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_COSTS))
    # SPEC 006: otomatik GBrain context injection kontrolleri (opsiyonel).
    # Eski YAML'lar (bu alanlar yok) default davranışla çalışır.
    inject_context: bool = True
    context_limit: int = 5
    # SPEC 003.2: opsiyonel özel sistem promptu. None → mevcut sabit
    # şablon (bit-uyumlu); str → prompt'un başına eklenir (planner içinde).
    llm_prompt: str | None = None
    # SPEC 009: opsiyonel model id (şu an anthropic backend'i kullanır).
    # None → env yolu (`ATLAS_LLM_MODEL`) veya varsayılan sabit.
    llm_model: str | None = None
    # SPEC 015: True + llm_prompt → Anthropic system alanı bloklar
    # listesi + cache_control ephemeral (5 dk hız/maliyet indirimi).
    prompt_cache: bool = False
    # SPEC 019: True → Anthropic Messages API streaming (SSE) — ilk
    # newline'da kes, algılanan gecikme düşer. Non-streaming davranışı
    # varsayılan (bit-uyumlu).
    stream: bool = False


def _require(spec: dict[str, object], key: str, kind: type) -> object:
    if key not in spec:
        raise SpecError(f"eksik alan: {key!r}")
    value = spec[key]
    if not isinstance(value, kind):
        raise SpecError(f"{key!r} beklenen tip {kind.__name__}, gelen {type(value).__name__}")
    return value


def load_goal(path: Path) -> Goal:
    """YAML dosyasını okur, doğrular ve `Goal` döner.

    Raises:
        SpecError: dosya yok / geçersiz YAML / eksik-yanlış alan.
    """
    if not path.is_file():
        raise SpecError(f"hedef dosyası bulunamadı: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SpecError(f"YAML parse hatası: {exc}") from exc
    if not isinstance(raw, dict):
        raise SpecError(f"hedef dosyası kök nesne olmalı, gelen: {type(raw).__name__}")

    goal = str(_require(raw, "goal", str))
    plan_kind_raw = str(_require(raw, "plan_kind", str))
    if plan_kind_raw not in _ALLOWED_PLAN_KINDS:
        raise SpecError(f"plan_kind bilinmiyor: {plan_kind_raw!r}")

    plan_steps_raw = raw.get("plan_steps", [])
    if not isinstance(plan_steps_raw, list) or not all(isinstance(s, str) for s in plan_steps_raw):
        raise SpecError("plan_steps: string listesi olmalı")
    plan_steps: tuple[str, ...] = tuple(plan_steps_raw)
    if plan_kind_raw == "static" and not plan_steps:
        raise SpecError("plan_kind=static için plan_steps boş olamaz")

    allow_raw = raw.get("action_allowlist", [])
    if not isinstance(allow_raw, list) or not all(isinstance(v, str) for v in allow_raw):
        raise SpecError("action_allowlist: string listesi olmalı")
    action_allowlist = frozenset(allow_raw)
    unknown = action_allowlist - _ALLOWED_VERBS
    if unknown:
        raise SpecError(f"action_allowlist bilinmeyen fiil(ler): {sorted(unknown)}")

    shell_regex: re.Pattern[str] | None = None
    if "shell" in action_allowlist:
        regex_raw = raw.get("shell_allow_regex")
        if not isinstance(regex_raw, str) or not regex_raw:
            raise SpecError("action_allowlist içinde 'shell' varsa shell_allow_regex zorunlu")
        try:
            shell_regex = re.compile(regex_raw)
        except re.error as exc:
            raise SpecError(f"shell_allow_regex derlenemedi: {exc}") from exc

    judge_kind_raw = str(_require(raw, "judge_kind", str))
    if judge_kind_raw not in _ALLOWED_JUDGE_KINDS:
        raise SpecError(f"judge_kind bilinmiyor: {judge_kind_raw!r}")
    judge_arg = str(_require(raw, "judge_arg", str))

    budget_raw = raw.get("budget", 50.0)
    if not isinstance(budget_raw, (int, float)) or budget_raw <= 0:
        raise SpecError(f"budget pozitif sayı olmalı, gelen: {budget_raw!r}")
    max_steps_raw = raw.get("max_steps", 8)
    if not isinstance(max_steps_raw, int) or max_steps_raw <= 0:
        raise SpecError(f"max_steps pozitif tamsayı olmalı, gelen: {max_steps_raw!r}")

    costs = dict(_DEFAULT_COSTS)
    costs_raw = raw.get("costs", {})
    if not isinstance(costs_raw, dict):
        raise SpecError("costs: sözlük olmalı")
    for k, v in costs_raw.items():
        if k not in _ALLOWED_VERBS:
            raise SpecError(f"costs bilinmeyen fiil: {k!r}")
        if not isinstance(v, (int, float)) or v < 0:
            raise SpecError(f"costs[{k!r}] negatif olmayan sayı olmalı")
        costs[k] = float(v)

    # SPEC 006: opsiyonel context injection alanları.
    inject_ctx_raw = raw.get("inject_context", True)
    if not isinstance(inject_ctx_raw, bool):
        raise SpecError(f"inject_context bool olmalı, gelen: {inject_ctx_raw!r}")
    ctx_limit_raw = raw.get("context_limit", 5)
    # bool int'in alt sınıfıdır — özellikle ele al.
    if isinstance(ctx_limit_raw, bool) or not isinstance(ctx_limit_raw, int):
        raise SpecError(f"context_limit pozitif tamsayı olmalı, gelen: {ctx_limit_raw!r}")
    if ctx_limit_raw <= 0 or ctx_limit_raw > _MAX_CONTEXT_LIMIT:
        raise SpecError(
            f"context_limit 1..{_MAX_CONTEXT_LIMIT} aralığında olmalı, gelen: {ctx_limit_raw}"
        )

    # SPEC 003.2: opsiyonel özel prompt (str veya None; boş string → None).
    llm_prompt_raw = raw.get("llm_prompt")
    llm_prompt: str | None
    if llm_prompt_raw is None:
        llm_prompt = None
    elif isinstance(llm_prompt_raw, str):
        llm_prompt = llm_prompt_raw if llm_prompt_raw else None
    else:
        raise SpecError(
            f"llm_prompt string olmalı, gelen: {type(llm_prompt_raw).__name__}"
        )

    # SPEC 009: opsiyonel model id (aynı 003.2 kalıbıyla).
    llm_model_raw = raw.get("llm_model")
    llm_model: str | None
    if llm_model_raw is None:
        llm_model = None
    elif isinstance(llm_model_raw, str):
        llm_model = llm_model_raw if llm_model_raw else None
    else:
        raise SpecError(
            f"llm_model string olmalı, gelen: {type(llm_model_raw).__name__}"
        )

    # SPEC 015: opsiyonel prompt caching (bool).
    prompt_cache_raw = raw.get("prompt_cache", False)
    if not isinstance(prompt_cache_raw, bool):
        raise SpecError(
            f"prompt_cache bool olmalı, gelen: {type(prompt_cache_raw).__name__}"
        )

    # SPEC 019: opsiyonel streaming (bool).
    stream_raw = raw.get("stream", False)
    if not isinstance(stream_raw, bool):
        raise SpecError(
            f"stream bool olmalı, gelen: {type(stream_raw).__name__}"
        )

    # Literal daraltması: yukarıda enum kontrolü yapıldı, tip güvenli.
    return Goal(
        goal=goal,
        plan_kind=plan_kind_raw,  # type: ignore[arg-type]
        plan_steps=plan_steps,
        action_allowlist=action_allowlist,
        shell_allow_regex=shell_regex,
        judge_kind=judge_kind_raw,  # type: ignore[arg-type]
        judge_arg=judge_arg,
        budget=float(budget_raw),
        max_steps=max_steps_raw,
        costs=costs,
        inject_context=inject_ctx_raw,
        context_limit=ctx_limit_raw,
        llm_prompt=llm_prompt,
        llm_model=llm_model,
        prompt_cache=prompt_cache_raw,
        stream=stream_raw,
    )

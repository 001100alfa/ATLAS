"""Orkestratör: ajan kaydı, bütçeli çağrı katmanı, P-A-O-R döngüsü.

loop  : Plan -> Act -> Observe -> Reflect; adım/bütçe sınırlı, audit'li.
call  : her eylem bütçe kontrolünden geçer -> kontrolsüz harcama yok.
spector (gözlemci): her döngü adımı telemetriye yazılır.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from atlas_core.security.audit import AuditLog


class StepKind(StrEnum):
    PLAN = "plan"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"


class BudgetExceededError(RuntimeError):
    """Adım veya maliyet bütçesi aşıldı."""


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Kayıtlı bir ajanın sözleşmesi."""

    name: str
    role: str
    allowed_tools: tuple[str, ...]
    max_cost: float  # birim: soyut kredi


class AgentRegistry:
    """Ad -> AgentSpec kayıt defteri; kayıtsız ajan çağrılamaz."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentSpec] = {}

    def register(self, spec: AgentSpec) -> None:
        if spec.name in self._agents:
            raise ValueError(f"Ajan zaten kayıtlı: {spec.name}")
        self._agents[spec.name] = spec

    def get(self, name: str) -> AgentSpec:
        if name not in self._agents:
            raise KeyError(f"Kayıtsız ajan: {name}")
        return self._agents[name]

    def names(self) -> list[str]:
        return sorted(self._agents)


@dataclass(slots=True)
class CallBudget:
    """Bütçeli çağrı katmanı: her eylem burada muhasebeleşir.

    SPEC 013: `charge_tokens` LLM token maliyetini kredi cinsinden
    ekler; fiyat 0 → no-op (env'sizken bütçe hiç değişmez).
    """

    limit: float
    spent: float = 0.0

    def charge(self, cost: float, what: str) -> None:
        if cost < 0:
            raise ValueError(f"Negatif maliyet: {what}")
        if self.spent + cost > self.limit:
            raise BudgetExceededError(
                f"Bütçe aşımı: {what} ({self.spent + cost:.1f} > {self.limit:.1f})"
            )
        self.spent += cost

    def charge_tokens(
        self,
        input_tokens: int,
        output_tokens: int,
        price_in: float,
        price_out: float,
    ) -> None:
        """SPEC 013: LLM token maliyeti bütçeye ekler (per million USD).

        Cost = `in * price_in / 1e6 + out * price_out / 1e6`. Fiyat
        0/negatif → no-op (bütçe hiç değişmez, 011 fail-safe kalıbı).
        Bütçe aşarsa `BudgetExceededError`.
        """
        if price_in <= 0 and price_out <= 0:
            return  # no-op: fiyat env'i yoksa/hatalıysa bütçe hiç değişmez
        cost = (
            input_tokens * max(price_in, 0.0) / 1_000_000
            + output_tokens * max(price_out, 0.0) / 1_000_000
        )
        if cost <= 0:
            return
        self.charge(cost, f"llm tokens (in={input_tokens} out={output_tokens})")


@dataclass(slots=True)
class LoopResult:
    done: bool
    steps: list[tuple[StepKind, str]] = field(default_factory=list)


Action = Callable[[str], tuple[str, float]]  # girdi -> (gözlem, maliyet)
Judge = Callable[[list[tuple[StepKind, str]]], bool]  # geçmiş -> bitti mi


def run_loop(
    goal: str,
    plan: Callable[[str, list[tuple[StepKind, str]]], str],
    act: Action,
    judge: Judge,
    budget: CallBudget,
    audit: AuditLog,
    max_steps: int = 8,
    actor: str = "atlas",
) -> LoopResult:
    """Plan-Act-Observe-Reflect döngüsü.

    Her tur audit'e yazılır; adım sınırı veya bütçe aşımı döngüyü
    güvenli şekilde durdurur (yarı-kalmış durum LoopResult'ta).
    """
    history: list[tuple[StepKind, str]] = []
    for step in range(max_steps):
        p = plan(goal, history)
        history.append((StepKind.PLAN, p))
        audit.record(actor, "plan", p)

        obs, cost = act(p)
        budget.charge(cost, f"adım {step}: {p[:40]}")
        history.append((StepKind.ACT, p))
        history.append((StepKind.OBSERVE, obs))
        audit.record(actor, "observe", obs)

        done = judge(history)
        history.append((StepKind.REFLECT, "hedef sağlandı" if done else "devam"))
        if done:
            audit.record(actor, "done", goal)
            return LoopResult(done=True, steps=history)

    audit.record(actor, "max_steps", goal)
    return LoopResult(done=False, steps=history)

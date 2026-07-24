"""ATLAS platform giriş noktası: beyin + orkestratör + güvenlik tek CLI'da.

Bu modül, `atlas_core` katmanlarını (GBrain, orchestrator, AuditLog,
scan_secrets) uçtan uca birbirine bağlayan tek çalıştırılabilir arayüzdür.

Örnekler:
    atlas context "kesit hesabı"          # göreve başlarken bağlam paketi
    atlas remember kesit "I-kesit formülleri" --link EN1993
    atlas recall "atalet momenti"
    atlas run "demo hedef"                 # bütçeli P-A-O-R döngüsü, audit'li
    atlas audit-verify                     # denetim zinciri bütünlüğü
    atlas scan src/                        # sır taraması (commit öncesi)

Yollar ortam değişkenleriyle geçersiz kılınabilir:
    ATLAS_VAULT  (varsayılan: ./vault)
    ATLAS_AUDIT  (varsayılan: ./.atlas/audit.jsonl)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from atlas_core.memory.gbrain import GBrain
from atlas_core.orchestrator.core import (
    AgentRegistry,
    AgentSpec,
    BudgetExceededError,
    CallBudget,
    StepKind,
    run_loop,
)
from atlas_core.security.audit import AuditLog, scan_secrets


def _vault_root() -> Path:
    return Path(os.environ.get("ATLAS_VAULT", "vault"))


def _audit_path() -> Path:
    return Path(os.environ.get("ATLAS_AUDIT", ".atlas/audit.jsonl"))


def _cmd_context(args: argparse.Namespace) -> int:
    brain = GBrain(_vault_root())
    print(brain.context_for(args.topic, limit=args.limit))
    return 0


def _cmd_remember(args: argparse.Namespace) -> int:
    brain = GBrain(_vault_root())
    path = brain.remember(
        args.name,
        args.content,
        links=tuple(args.link or ()),
        tags=tuple(args.tag or ()),
    )
    print(f"Yazıldı: {path}")
    return 0


def _cmd_recall(args: argparse.Namespace) -> int:
    brain = GBrain(_vault_root())
    hits = brain.recall(args.query, limit=args.limit)
    if not hits:
        print(f"(kayıt yok: {args.query!r})")
        return 0
    for h in hits:
        print(f"{h.score:6.2f}  {h.name:24s}  {h.snippet}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    """Platformun tümünü bağlayan demo: kayıtlı ajan + bütçe + audit + P-A-O-R.

    Gerçek eylem yerine yer tutucu (echo) kullanır; amaç orkestratör
    döngüsünün beyin/güvenlik katmanıyla uçtan uca çalıştığını göstermektir.
    """
    audit = AuditLog(_audit_path())
    registry = AgentRegistry()
    registry.register(
        AgentSpec(
            name="echo",
            role="demo",
            allowed_tools=("print",),
            max_cost=args.budget,
        )
    )
    spec = registry.get("echo")
    budget = CallBudget(limit=spec.max_cost)

    step_no = {"i": 0}

    def plan(goal: str, history: list[tuple[StepKind, str]]) -> str:
        step_no["i"] += 1
        return f"{goal} — adım {step_no['i']}"

    def act(p: str) -> tuple[str, float]:
        return (f"[{spec.name}] {p}", args.step_cost)

    def judge(history: list[tuple[StepKind, str]]) -> bool:
        acts = sum(1 for kind, _ in history if kind is StepKind.ACT)
        return acts >= int(args.steps)

    try:
        result = run_loop(
            goal=args.goal,
            plan=plan,
            act=act,
            judge=judge,
            budget=budget,
            audit=audit,
            max_steps=args.max_steps,
            actor="atlas-cli",
        )
    except BudgetExceededError as exc:
        print(f"BÜTÇE AŞIMI: {exc}", file=sys.stderr)
        return 3

    for kind, text in result.steps:
        print(f"  {kind.value:8s} {text}")
    print(f"\ndone={result.done}  harcanan={budget.spent:.1f}/{budget.limit:.1f}")
    print(f"audit: {audit.path}  (zincir geçerli={audit.verify()})")
    return 0 if result.done else 4


def _cmd_audit_verify(args: argparse.Namespace) -> int:
    audit = AuditLog(_audit_path())
    ok = audit.verify()
    print(f"Denetim zinciri: {'GEÇERLİ' if ok else 'BOZULMUŞ'} ({audit.path})")
    return 0 if ok else 1


def _cmd_scan(args: argparse.Namespace) -> int:
    target = Path(args.path)
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    total = 0
    for f in files:
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, masked in scan_secrets(text):
            print(f"{f}: {name} -> {masked}")
            total += 1
    if total:
        print(f"\n{total} olası sır bulundu — commit DURDURULMALI.", file=sys.stderr)
        return 1
    print("Sır bulunamadı.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ctx = sub.add_parser("context", help="Göreve bağlam paketi üret")
    p_ctx.add_argument("topic")
    p_ctx.add_argument("--limit", type=int, default=5)
    p_ctx.set_defaults(func=_cmd_context)

    p_rem = sub.add_parser("remember", help="Beyne bilgi yaz")
    p_rem.add_argument("name")
    p_rem.add_argument("content")
    p_rem.add_argument("--link", action="append", help="[[wikilink]] hedefi")
    p_rem.add_argument("--tag", action="append", help="#etiket")
    p_rem.set_defaults(func=_cmd_remember)

    p_rec = sub.add_parser("recall", help="Beyinden geri çağır")
    p_rec.add_argument("query")
    p_rec.add_argument("--limit", type=int, default=5)
    p_rec.set_defaults(func=_cmd_recall)

    p_run = sub.add_parser("run", help="Bütçeli P-A-O-R döngüsü (demo)")
    p_run.add_argument("goal")
    p_run.add_argument("--steps", type=int, default=3, help="hedefe kaç ACT yeter")
    p_run.add_argument("--max-steps", type=int, default=8)
    p_run.add_argument("--budget", type=float, default=100.0)
    p_run.add_argument("--step-cost", type=float, default=10.0)
    p_run.set_defaults(func=_cmd_run)

    p_av = sub.add_parser("audit-verify", help="Denetim zinciri bütünlüğü")
    p_av.set_defaults(func=_cmd_audit_verify)

    p_scan = sub.add_parser("scan", help="Sır taraması (dosya/dizin)")
    p_scan.add_argument("path")
    p_scan.set_defaults(func=_cmd_scan)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

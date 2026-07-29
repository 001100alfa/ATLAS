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
from datetime import datetime
from pathlib import Path

from atlas_core.memory.archive import archive_task
from atlas_core.memory.gbrain import GBrain
from atlas_core.memory.vault import Vault
from atlas_core.orchestrator.actions import ActionDeniedError, make_action
from atlas_core.orchestrator.core import (
    AgentRegistry,
    AgentSpec,
    BudgetExceededError,
    CallBudget,
    StepKind,
    run_loop,
)
from atlas_core.orchestrator.goals import Goal, SpecError, load_goal
from atlas_core.orchestrator.judges import make_judge
from atlas_core.orchestrator.planner import (
    LLMPlannerError,
    PlannerExhaustedError,
    make_planner,
)
from atlas_core.security.audit import AuditLog, scan_secrets
from atlas_core.workflows.engine import WorkflowEngine, WorkflowError
from atlas_core.workflows.handlers import HandlerError, register_builtins


def _sandbox_root() -> Path:
    return Path(os.environ.get("ATLAS_SANDBOX", ".atlas/sandbox"))


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


def _context_enabled(goal: Goal) -> bool:
    """SPEC 006 FR2: context injection açık mı?

    Sıra: env `ATLAS_CONTEXT=off` → False, `Goal.inject_context is False` →
    False, `plan_kind=="static"` → False (static görevlerde gerek yok).
    Aksi hâlde True.
    """
    if os.environ.get("ATLAS_CONTEXT", "on").lower() == "off":
        return False
    if not goal.inject_context:
        return False
    if goal.plan_kind == "static":
        return False
    return True


def _compute_context(goal: Goal) -> tuple[str | None, str]:
    """GBrain.context_for'u çağırır; (context, görünürlük etiketi) döner.

    FR6: GBrain hatası görevi kırmasın — stderr'e uyarı, ctx=None, devam.
    """
    try:
        brain = GBrain(_vault_root())
        ctx = brain.context_for(goal.goal, limit=goal.context_limit)
    except Exception as exc:  # noqa: BLE001 — FR6 hata izolasyonu; görevi bloklamaz
        print(f"UYARI: GBrain context alınamadı: {exc}", file=sys.stderr)
        return None, "yok (hata)"
    if not ctx or ctx.startswith("(GBrain:"):
        return None, "yok"
    # Basit satır sayımı: "- [[..]]" ile başlayan not satırları
    n = sum(1 for line in ctx.splitlines() if line.startswith("- [["))
    return ctx, f"{n} not enjekte edildi"


def _cmd_run_goal(args: argparse.Namespace) -> int:
    """SPEC 002: `--goal-file` verildiğinde gerçek görev sürücüsü.

    goal YAML'ini yükler, sandbox'i kurar, planner+action+judge'u
    fabrikadan alır, run_loop'u sürer. ActionDeniedError yakalanır,
    audit'e 'denied' kaydi düşer, exit 5.

    SPEC 006: `_context_enabled(goal)` True ise GBrain.context_for(goal.goal)
    tek kez çağrılıp planner fabrikasına geçirilir; static görevler ve
    `ATLAS_CONTEXT=off` durumu için GBrain hiç instantiate edilmez.
    """
    try:
        goal = load_goal(Path(args.goal_file))
    except SpecError as exc:
        print(f"SPEC HATASI: {exc}", file=sys.stderr)
        return 2

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    goal_id = f"{Path(args.goal_file).stem}-{run_id}"
    sandbox = _sandbox_root() / goal_id
    sandbox.mkdir(parents=True, exist_ok=True)

    # SPEC 006: context enjeksiyonu (görev başında bir kez)
    if _context_enabled(goal):
        ctx, ctx_label = _compute_context(goal)
        print(f"Bağlam: {ctx_label}")
    else:
        ctx = None
        print("Bağlam: (kapalı)")

    audit = AuditLog(_audit_path())
    budget = CallBudget(limit=goal.budget)
    last_exit: dict[str, int] = {}
    try:
        plan = make_planner(goal, context=ctx)  # fabrika: LLM bin yok → LLMPlannerError
    except LLMPlannerError as exc:
        audit.record("atlas-run", "llm_error", str(exc)[:200])
        print(f"LLM PLANNER HATASI: {exc}", file=sys.stderr)
        return 7
    act = make_action(goal, sandbox, last_exit)
    judge = make_judge(goal, sandbox, last_exit)

    try:
        result = run_loop(
            goal=goal.goal,
            plan=plan,
            act=act,
            judge=judge,
            budget=budget,
            audit=audit,
            max_steps=goal.max_steps,
            actor="atlas-run",
        )
    except ActionDeniedError as exc:
        audit.record("atlas-run", "denied", str(exc))
        print(f"REDDEDİLDİ: {exc}", file=sys.stderr)
        return 5
    except PlannerExhaustedError as exc:
        audit.record("atlas-run", "planner_exhausted", str(exc))
        print(f"PLAN BİTTİ: {exc}", file=sys.stderr)
        return 4
    except LLMPlannerError as exc:
        audit.record("atlas-run", "llm_error", str(exc)[:200])
        print(f"LLM PLANNER HATASI: {exc}", file=sys.stderr)
        return 7
    except BudgetExceededError as exc:
        print(f"BÜTÇE AŞIMI: {exc}", file=sys.stderr)
        return 3

    for kind, text in result.steps:
        print(f"  {kind.value:8s} {text[:120]}")
    print(f"\ndone={result.done}  harcanan={budget.spent:.1f}/{budget.limit:.1f}")
    print(f"sandbox: {sandbox}")
    print(f"audit: {audit.path}  (zincir geçerli={audit.verify()})")
    return 0 if result.done else 4


def _cmd_run(args: argparse.Namespace) -> int:
    """Platformun tümünü bağlayan demo: kayıtlı ajan + bütçe + audit + P-A-O-R.

    `--goal-file` verilirse gerçek görev sürücüsüne (`_cmd_run_goal`) dallanır.
    Aksi halde eski yer tutucu (echo) demo davranışı korunur (regresyon).
    """
    if args.goal_file:
        return _cmd_run_goal(args)
    if not args.goal:
        print("kullanım: atlas run <hedef> | atlas run --goal-file <yaml>", file=sys.stderr)
        return 2
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


def _cmd_reindex(args: argparse.Namespace) -> int:
    """SPEC 005: `atlas reindex [--full]` — GBrain FTS indeksini yeniden kurar."""
    brain = GBrain(_vault_root())
    if not brain.index.is_fts_available():
        print("UYARI: SQLite FTS5 yok — reindex atlandı (fallback modda çalışır).",
              file=sys.stderr)
        return 0
    stats = brain.index.rebuild() if args.full else brain.index.ensure_fresh()
    print(f"indexed={stats.indexed} skipped={stats.skipped} "
          f"removed={stats.removed} elapsed={stats.elapsed_s:.3f}s")
    return 0


def _cmd_workflow_run(args: argparse.Namespace) -> int:
    """SPEC 004: `atlas workflow run <yaml> [--dry-run]`."""
    yaml_path = Path(args.yaml)
    if not yaml_path.is_file():
        print(f"SPEC HATASI: workflow dosyası yok: {yaml_path}", file=sys.stderr)
        return 2
    audit = AuditLog(_audit_path())
    engine = WorkflowEngine(audit)
    register_builtins(engine, dry_run=args.dry_run)
    try:
        results = engine.run(yaml_path)
    except HandlerError as exc:
        audit.record("workflow", "error", str(exc)[:200])
        print(f"HANDLER HATASI: {exc}", file=sys.stderr)
        return 6
    except WorkflowError as exc:
        audit.record("workflow", "error", str(exc)[:200])
        print(f"WORKFLOW HATASI: {exc}", file=sys.stderr)
        return 6
    for r in results:
        print(f"  {r.step:20s} {r.output[:100]}")
    print(f"\nOK: {len(results)} adım tamamlandı  audit: {audit.path}")
    return 0


def _cmd_audit_verify(args: argparse.Namespace) -> int:
    audit = AuditLog(_audit_path())
    ok = audit.verify()
    print(f"Denetim zinciri: {'GEÇERLİ' if ok else 'BOZULMUŞ'} ({audit.path})")
    return 0 if ok else 1


def _read_ship_summary(task_dir: Path) -> str:
    """SPEC 007 FR6: 09-ship.md'nin ilk paragrafını okur, yoksa fallback.

    Fallback: `"<task> arşivlendi"`.
    """
    ship = task_dir / "09-ship.md"
    if not ship.is_file():
        return f"{task_dir.name} arşivlendi"
    try:
        raw = ship.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f"{task_dir.name} arşivlendi"
    # H1 (# ...) satırlarını atla; ilk boş satıra kadar olan bloğu al.
    lines = raw.splitlines()[:50]
    body: list[str] = []
    seen_content = False
    for ln in lines:
        if ln.startswith("#"):
            continue
        stripped = ln.strip()
        if not stripped:
            if seen_content:
                break
            continue
        seen_content = True
        body.append(stripped)
    text = " ".join(body).strip()
    return text or f"{task_dir.name} arşivlendi"


def _cmd_archive(args: argparse.Namespace) -> int:
    """SPEC 007: `atlas archive <task> [--apply] [--summary TEXT]`.

    Dry-run varsayılan (yıkıcı işlem). `--apply` ile gerçek arşivleme:
    tar.gz + vault notu + klasör silme + audit kaydı.
    """
    tasks_root = Path(args.tasks_root)
    archive_root = Path(args.archive_root)
    task_dir = tasks_root / args.task
    if not task_dir.is_dir():
        print(f"SPEC HATASI: görev klasörü yok: {task_dir}", file=sys.stderr)
        return 2

    tar_target = archive_root / f"{args.task}-{datetime.now().date().isoformat()}.tar.gz"
    vault_root = _vault_root()
    vault_note = vault_root / "tasks" / f"task-{args.task}.md"

    if not args.apply:
        print("[dry-run] arşivleme planı:")
        print(f"  kaynak: {task_dir}")
        print(f"  hedef:  {tar_target}")
        print(f"  vault:  {vault_note}")
        print(f"Uygulamak için: atlas archive {args.task} --apply")
        return 0

    summary = args.summary or _read_ship_summary(task_dir)
    audit = AuditLog(_audit_path())
    try:
        vault = Vault(vault_root)
        tar_path = archive_task(task_dir, archive_root, vault, summary)
    except (OSError, FileNotFoundError) as exc:
        audit.record("atlas-archive", "error", str(exc)[:200])
        print(f"ARŞİV HATASI: {exc}", file=sys.stderr)
        return 6

    audit.record("atlas-archive", "archive", args.task)
    print(f"arşivlendi: {tar_path}")
    print(f"vault:      {vault_note}")
    print(f"kaldırıldı: {task_dir}")
    return 0


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

    p_run = sub.add_parser("run", help="Bütçeli P-A-O-R döngüsü")
    p_run.add_argument("goal", nargs="?", default=None, help="echo demo için hedef metni")
    p_run.add_argument("--goal-file", default=None, help="YAML hedef dosyası (SPEC 002)")
    p_run.add_argument("--run-id", default=None, help="sandbox alt dizini için sabit ad (test)")
    p_run.add_argument("--steps", type=int, default=3, help="echo demo: kaç ACT yeter")
    p_run.add_argument("--max-steps", type=int, default=8)
    p_run.add_argument("--budget", type=float, default=100.0)
    p_run.add_argument("--step-cost", type=float, default=10.0)
    p_run.set_defaults(func=_cmd_run)

    p_rx = sub.add_parser("reindex", help="GBrain FTS indeksini yeniden kur")
    p_rx.add_argument("--full", action="store_true", help="mevcut indeksi sil, sıfırdan kur")
    p_rx.set_defaults(func=_cmd_reindex)

    p_wf = sub.add_parser("workflow", help="YAML workflow yürüt")
    wf_sub = p_wf.add_subparsers(dest="wf_cmd", required=True)
    p_wf_run = wf_sub.add_parser("run", help="workflow YAML'ini çalıştır")
    p_wf_run.add_argument("yaml", help="workflow YAML yolu")
    p_wf_run.add_argument("--dry-run", action="store_true", help="handler'lar no-op çalışır")
    p_wf_run.set_defaults(func=_cmd_workflow_run)

    p_av = sub.add_parser("audit-verify", help="Denetim zinciri bütünlüğü")
    p_av.set_defaults(func=_cmd_audit_verify)

    p_scan = sub.add_parser("scan", help="Sır taraması (dosya/dizin)")
    p_scan.add_argument("path")
    p_scan.set_defaults(func=_cmd_scan)

    p_arc = sub.add_parser("archive", help="Tamamlanmış görevi arşive taşı")
    p_arc.add_argument("task", help="pipeline/tasks/ altındaki klasör adı")
    p_arc.add_argument("--apply", action="store_true",
                       help="dry-run yerine gerçek taşımayı çalıştır (yıkıcı)")
    p_arc.add_argument("--summary", default=None,
                       help="vault notunun gövdesi (yoksa 09-ship.md okunur)")
    p_arc.add_argument("--tasks-root", default="pipeline/tasks",
                       help="görevlerin bulunduğu kök dizin")
    p_arc.add_argument("--archive-root", default="archive",
                       help="tar.gz'lerin yazılacağı kök dizin")
    p_arc.set_defaults(func=_cmd_archive)

    args = parser.parse_args(argv)
    # Windows konsolu (cp1254) Türkçe/üstsimge çıktıyı bozabilir; UTF-8'e sabitle.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

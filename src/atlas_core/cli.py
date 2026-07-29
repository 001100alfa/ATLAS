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
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

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
    _read_retry_env,
    make_planner,
    make_retrying_planner,
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


def _read_llm_prices() -> tuple[float, float]:
    """SPEC 013: `(price_in, price_out)` per million USD — env'den.

    Parse hatası → `(0.0, 0.0)` (fail-safe, 011 kalıbıyla simetrik).
    """
    try:
        pin = float(os.environ.get("ATLAS_LLM_PRICE_IN", "0") or "0")
        pout = float(os.environ.get("ATLAS_LLM_PRICE_OUT", "0") or "0")
    except ValueError:
        return 0.0, 0.0
    return max(pin, 0.0), max(pout, 0.0)


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

    # SPEC 027: YAML'ı .atlas/runs/<goal_id>.yaml'a kopyala (replay için).
    _archive_goal_yaml(Path(args.goal_file), goal_id)

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
    # SPEC 013 + 015.1: anthropic backend usage → CallBudget.charge_tokens
    # (fiyat env yoksa no-op; charge_tokens içindeki fail-safe).
    # 4-arg: (input, output, cache_creation, cache_read).
    price_in, price_out = _read_llm_prices()

    def _on_usage(
        in_tok: int, out_tok: int, cache_c: int, cache_r: int
    ) -> None:
        budget.charge_tokens(
            in_tok, out_tok, price_in, price_out,
            cache_creation=cache_c, cache_read=cache_r,
        )

    try:
        inner = make_planner(
            goal, context=ctx, on_usage=_on_usage
        )  # fabrika: LLM bin yok → LLMPlannerError
    except LLMPlannerError as exc:
        audit.record("atlas-run", "llm_error", str(exc)[:200])
        print(f"LLM PLANNER HATASI: {exc}", file=sys.stderr)
        return 7
    # SPEC 008: opsiyonel retry sarmalayıcı (env kapalıysa kimlik-geçiş).
    retries, backoff_s = _read_retry_env()
    plan = make_retrying_planner(inner, retries, backoff_s)
    # SPEC 020: --dry-run → action stub + judge single-step done.
    dry_run = getattr(args, "dry_run", False)
    act: Callable[[str], tuple[str, float]]
    judge: Callable[[list[tuple[StepKind, str]]], bool]
    if dry_run:
        print("MOD: dry-run — action yürütme kapalı")
        audit.record("atlas-run", "dry_run", goal.goal[:200])
        act = lambda p: (f"[dry-run] eylem yürütülmedi: {p}", 0.0)  # noqa: E731
        judge = lambda _history: True  # noqa: E731
    else:
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
    """SPEC 007+012: `atlas archive <task> | --all [--apply] [--yes] ...`.

    Dry-run varsayılan (yıkıcı işlem). Tekil: `--apply` yeter. Toplu:
    `--all --apply --yes` (çift onay).
    """
    if getattr(args, "all", False):
        return _cmd_archive_all(args)
    if not args.task:
        print("SPEC HATASI: <task> ya da --all zorunlu", file=sys.stderr)
        return 2

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


def _iter_archive_candidates(
    tasks_root: Path, age_days: float | None = None
) -> list[Path]:
    """SPEC 012 M2 + SPEC 017: `09-ship.md` dosyası olan görev klasörleri.

    `age_days` verilirse (SPEC 017): ship.md mtime'ı `age_days` günden
    eski olanlar seçilir; taze görevler atlanır. `None` → 012 davranışı
    (tümü).
    """
    if not tasks_root.is_dir():
        return []
    now = datetime.now().timestamp()
    threshold = now - (age_days * 86400) if age_days is not None else None
    out: list[Path] = []
    for child in sorted(tasks_root.iterdir()):
        if not child.is_dir():
            continue
        ship = child / "09-ship.md"
        if not ship.is_file():
            continue
        if threshold is not None and ship.stat().st_mtime > threshold:
            continue  # ship.md hâlâ taze → atla
        out.append(child)
    return out


def _read_archive_age_env() -> float:
    """SPEC 017: `ATLAS_ARCHIVE_AGE_DAYS` env (varsayılan 7).

    Parse hatası → 7 (fail-safe).
    """
    try:
        v = float(os.environ.get("ATLAS_ARCHIVE_AGE_DAYS", "7") or "7")
    except ValueError:
        return 7.0
    return max(v, 0.0)


def _cmd_archive_all(args: argparse.Namespace) -> int:
    """SPEC 012 + 017: `atlas archive --all [--auto] [--apply --yes]`.

    Aday: `pipeline/tasks/*/09-ship.md` olanlar (tamamlanmış).
    `--auto` (SPEC 017) verilirse ship.md mtime'ı
    `ATLAS_ARCHIVE_AGE_DAYS` (varsayılan 7) günden eski olanlar seçilir.
    `--apply` **yalnız** `--yes` ile birlikte gerçek toplu iş yapar.
    Fail-fast: ilk hata → dur, raporla.
    """
    tasks_root = Path(args.tasks_root)
    archive_root = Path(args.archive_root)
    age_days: float | None = None
    if getattr(args, "auto", False):
        age_days = _read_archive_age_env()
    candidates = _iter_archive_candidates(tasks_root, age_days=age_days)

    if not args.apply:
        age_suffix = f" (auto, >{age_days:g} gün)" if age_days is not None else ""
        print(f"[dry-run] toplu arşivleme adayları{age_suffix}: {len(candidates)} görev")
        for d in candidates:
            print(f"  - {d.name}")
        if candidates:
            hint = "atlas archive --all --apply --yes"
            if age_days is not None:
                hint = "atlas archive --all --auto --apply --yes"
            print(f"Uygulamak için: {hint}")
        return 0

    if not getattr(args, "yes", False):
        print(
            "TOPLU ARŞİV: --yes ile onaylayın (çoklu yıkıcı işlem)",
            file=sys.stderr,
        )
        return 2

    audit = AuditLog(_audit_path())
    vault_root = _vault_root()
    vault = Vault(vault_root)
    succeeded: list[str] = []
    failed: tuple[str, str] | None = None

    for d in candidates:
        summary = _read_ship_summary(d)
        try:
            archive_task(d, archive_root, vault, summary)
        except (OSError, FileNotFoundError) as exc:
            failed = (d.name, str(exc)[:200])
            audit.record("atlas-archive", "error", f"{d.name}: {failed[1]}")
            break
        audit.record("atlas-archive", "archive", d.name)
        succeeded.append(d.name)

    total = len(candidates)
    done = len(succeeded)
    skipped = [d.name for d in candidates[done + (1 if failed else 0):]]

    print(f"arşivlendi: {done}/{total} görev")
    if succeeded:
        print(f"başarılı: {', '.join(succeeded)}")
    if failed:
        print(f"başarısız: {failed[0]} — {failed[1]}", file=sys.stderr)
    if skipped:
        print(f"atlanan: {', '.join(skipped)}")
    return 6 if failed else 0


def _runs_dir() -> Path:
    """SPEC 027: `ATLAS_RUNS_DIR` (varsayılan `.atlas/runs`)."""
    override = os.environ.get("ATLAS_RUNS_DIR", "").strip()
    if override:
        return Path(override)
    return Path(".atlas/runs")


def _archive_goal_yaml(goal_file: Path, run_id: str) -> Path | None:
    """SPEC 027: YAML'ı `.atlas/runs/<run-id>.yaml` olarak kopyala.

    Hata sessiz — ana akışı bloklamaz.
    """
    try:
        target_dir = _runs_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{run_id}.yaml"
        target.write_text(
            goal_file.read_text(encoding="utf-8", errors="replace"),
            encoding="utf-8",
        )
        return target
    except OSError:
        return None


def _extract_goal_from_yaml(path: Path, max_len: int = 60) -> str:
    """SPEC 028: YAML'ın ilk `^goal:` satırından hedef metni çıkar.

    Bulunamazsa `""` döner. Uzunsa `max_len` char'da keser + `…`.
    Hata sessiz — listelemeyi bloklamaz.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("goal:"):
            continue
        goal = line[len("goal:"):].strip()
        # YAML'da tırnaklı olabilir
        if len(goal) >= 2 and goal[0] == goal[-1] and goal[0] in ("'", '"'):
            goal = goal[1:-1]
        if len(goal) > max_len:
            goal = goal[: max_len - 1] + "…"
        return goal
    return ""


def _collect_replay_runs(limit: int) -> list[dict[str, Any]]:
    """SPEC 028: `.atlas/runs/*.yaml` mtime desc → liste.

    Her kayıt `{run_id, mtime (YYYY-MM-DD HH:MM:SS), goal}`.
    """
    import datetime as _dt

    runs_dir = _runs_dir()
    if not runs_dir.is_dir():
        return []
    yamls = [p for p in runs_dir.iterdir() if p.is_file() and p.suffix == ".yaml"]
    yamls.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    yamls = yamls[:limit]
    out: list[dict[str, Any]] = []
    for p in yamls:
        try:
            mtime_s = _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except (OSError, OverflowError, ValueError):
            mtime_s = "?"
        out.append({
            "run_id": p.stem,
            "mtime": mtime_s,
            "goal": _extract_goal_from_yaml(p),
        })
    return out


def _cmd_replay_list(args: argparse.Namespace) -> int:
    """SPEC 028: `atlas replay --list` — kayıtlı run'ları göster."""
    import json as _json

    runs = _collect_replay_runs(args.limit)
    if args.json:
        print(_json.dumps(runs, ensure_ascii=False))
        return 0

    if not runs:
        print("(hiç kayıt yok)")
        return 0

    print(f"=== ATLAS replay — kayıtlı {len(runs)} run ===")
    print()
    print(f"  {'#':<3} {'run_id':<32} {'mtime':<20} {'goal':<60}")
    for i, r in enumerate(runs, start=1):
        print(
            f"  {i:<3} {r['run_id'][:32]:<32} "
            f"{r['mtime']:<20} {r['goal'][:60]:<60}"
        )
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    """SPEC 027 + 028: `atlas replay [<run-id>|--list]`.

    `--list` → mevcut run'ları listele (`_cmd_replay_list`).
    Aksi → 027 davranışı: kopyayı bulup çalıştır.
    """
    # SPEC 028: --list dallanması
    if getattr(args, "list", False):
        return _cmd_replay_list(args)

    # SPEC 028: --list yok VE run_id yok → açık hata
    if not args.run_id:
        print(
            "SPEC HATASI: run-id ya da --list gerekli",
            file=sys.stderr,
        )
        return 2

    yaml_path = _runs_dir() / f"{args.run_id}.yaml"
    if not yaml_path.is_file():
        print(
            f"SPEC HATASI: run bulunamadı: {args.run_id} "
            f"({yaml_path})",
            file=sys.stderr,
        )
        return 2
    # `_cmd_run_goal`'a args namespace ile geç.
    replay_args = argparse.Namespace(
        goal_file=str(yaml_path),
        run_id=args.new_run_id,
        dry_run=getattr(args, "dry_run", False),
    )
    return _cmd_run_goal(replay_args)


def _load_dotenv(path: Path) -> int:
    """SPEC 022: `.env` dosyasını el ile parse edip `os.environ`'a yükle.

    - Dosya yoksa sessiz no-op (0 döner).
    - Her satır `KEY=VALUE`; `#` yorum; boş satır atla.
    - `VALUE` etrafında `"..."` veya `'...'` varsa tırnak sıyrılır.
    - Mevcut env değişkenini **override etmez** (shell env üstünde).

    Döner: yüklenen değişken sayısı (test için).
    """
    if not path.is_file():
        return 0
    loaded = 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if key not in os.environ:
            os.environ[key] = val
            loaded += 1
    return loaded


def _mask_secret(value: str, keep_prefix: int = 3, keep_suffix: int = 3) -> str:
    """API key maskele: `sk-...***abc`."""
    if not value:
        return "(yok)"
    if len(value) <= keep_prefix + keep_suffix:
        return "***"
    return f"{value[:keep_prefix]}***{value[-keep_suffix:]}"


_PING_TIMEOUT_S = 10
_PING_MAX_TOKENS = 8


def _run_anthropic_ping(warnings: list[str]) -> dict[str, Any] | None:
    """SPEC 021.2: minimum 'hello' request'i at, latency + usage döner.

    Backend anthropic değilse None + warnings uyarı.
    Hata (URLError, HTTPError, timeout) → None + warnings uyarı.
    Başarılı: `{"latency_ms", "input_tokens", "output_tokens",
    "cache_creation_input_tokens", "cache_read_input_tokens",
    "cost_estimate"}`.
    """
    import json as _json
    import time as _time
    from urllib import error as _urllib_error
    from urllib import request as _urllib_request

    backend = os.environ.get("ATLAS_LLM", "stub")
    if backend != "anthropic":
        warnings.append("--ping yalnız anthropic backend'de çalışır")
        return None

    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        warnings.append("ping başarısız: ANTHROPIC_API_KEY yok")
        return None

    url = (
        os.environ.get("ATLAS_LLM_ANTHROPIC_URL", "").strip()
        or "https://api.anthropic.com/v1/messages"
    )
    model = (
        os.environ.get("ATLAS_LLM_MODEL", "").strip()
        or "claude-3-5-sonnet-latest"
    )
    body = _json.dumps({
        "model": model,
        "max_tokens": _PING_MAX_TOKENS,
        "messages": [{"role": "user", "content": "hello"}],
    }).encode("utf-8")
    req = _urllib_request.Request(  # noqa: S310 - env kontrollü URL
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    t0 = _time.monotonic()
    try:
        with _urllib_request.urlopen(req, timeout=_PING_TIMEOUT_S) as resp:  # noqa: S310
            raw = resp.read()
    except _urllib_error.HTTPError as exc:
        warnings.append(f"ping başarısız: HTTP {exc.code}")
        return None
    except _urllib_error.URLError as exc:
        warnings.append(f"ping başarısız: {exc.reason}")
        return None
    except TimeoutError:
        warnings.append(f"ping başarısız: timeout ({_PING_TIMEOUT_S}s)")
        return None
    latency_ms = int((_time.monotonic() - t0) * 1000)

    try:
        data = _json.loads(raw.decode("utf-8", errors="replace"))
    except _json.JSONDecodeError:
        warnings.append("ping başarısız: geçersiz JSON")
        return None

    # 015.1 4-tuple ile fiyat hesabı
    from atlas_core.orchestrator.planner import _extract_usage, _fmt_cost
    in_tok, out_tok, cc, cr = _extract_usage(data)
    cost = _fmt_cost(in_tok, out_tok, cc, cr)
    return {
        "latency_ms": latency_ms,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cache_creation_input_tokens": cc,
        "cache_read_input_tokens": cr,
        "cost_estimate": cost,
    }


def _collect_doctor_report() -> dict[str, Any]:
    """SPEC 021 + 021.1: env sağlık özetini yapılandırılmış dict olarak topla.

    Şema:
    ```
    {
      "backend": {...},
      "retry_pricing": {...},
      "storage": {...},
      "warnings": [str, ...]
    }
    ```
    API key maskeli. Uyarılar warnings listesinde.
    """
    import shutil as _shutil

    warnings: list[str] = []
    backend = os.environ.get("ATLAS_LLM", "stub")
    supported = ("stub", "claude", "anthropic", "acp")

    backend_info: dict[str, Any] = {"ATLAS_LLM": backend}
    if backend not in supported:
        warnings.append(
            f"bilinmeyen backend: {backend} (desteklenen: {', '.join(supported)})"
        )
    if backend == "claude":
        override = os.environ.get("ATLAS_LLM_CLAUDE_BIN", "").strip()
        if override and os.path.isfile(override):
            backend_info["claude_bin"] = override
            backend_info["claude_bin_source"] = "override"
        else:
            found = _shutil.which("claude")
            if found:
                backend_info["claude_bin"] = found
                backend_info["claude_bin_source"] = "PATH"
            else:
                warnings.append(
                    "claude bin bulunamadı: PATH'e ekleyin veya "
                    "ATLAS_LLM_CLAUDE_BIN"
                )
    if backend == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if key:
            backend_info["ANTHROPIC_API_KEY"] = _mask_secret(key)
        else:
            backend_info["ANTHROPIC_API_KEY"] = ""
            warnings.append("ANTHROPIC_API_KEY yok")
        backend_info["ATLAS_LLM_MODEL"] = (
            os.environ.get("ATLAS_LLM_MODEL", "").strip()
            or "claude-3-5-sonnet-latest"
        )
        backend_info["ATLAS_LLM_ANTHROPIC_URL"] = (
            os.environ.get("ATLAS_LLM_ANTHROPIC_URL", "").strip()
            or "https://api.anthropic.com/v1/messages"
        )
    if backend == "acp":
        override = os.environ.get("ATLAS_LLM_ACP_BIN", "").strip()
        if override and os.path.isfile(override):
            backend_info["acp_bin"] = override
            backend_info["acp_bin_source"] = "override"
        else:
            found = _shutil.which("acp-agent")
            if found:
                backend_info["acp_bin"] = found
                backend_info["acp_bin_source"] = "PATH"
            else:
                warnings.append(
                    "acp agent bin bulunamadı: PATH'e ekleyin veya "
                    "ATLAS_LLM_ACP_BIN"
                )
        args_extra = os.environ.get("ATLAS_LLM_ACP_ARGS", "").strip()
        if args_extra:
            backend_info["ATLAS_LLM_ACP_ARGS"] = args_extra
    backend_info["ATLAS_LLM_TIMEOUT"] = os.environ.get("ATLAS_LLM_TIMEOUT", "60")

    retry_pricing: dict[str, Any] = {
        "ATLAS_LLM_RETRIES": os.environ.get("ATLAS_LLM_RETRIES", "0"),
        "ATLAS_LLM_BACKOFF": os.environ.get("ATLAS_LLM_BACKOFF", "1.0"),
        "ATLAS_LLM_JITTER": os.environ.get("ATLAS_LLM_JITTER", "0"),
        "ATLAS_LLM_PRICE_IN": os.environ.get("ATLAS_LLM_PRICE_IN", "").strip(),
        "ATLAS_LLM_PRICE_OUT": os.environ.get("ATLAS_LLM_PRICE_OUT", "").strip(),
        "ATLAS_LLM_TRACE": os.environ.get("ATLAS_LLM_TRACE", "").strip(),
        "ATLAS_LLM_OBS_CHARS": os.environ.get("ATLAS_LLM_OBS_CHARS", "200"),
    }

    storage: dict[str, Any] = {
        "ATLAS_VAULT": str(_vault_root()),
        "ATLAS_AUDIT": str(_audit_path()),
        "ATLAS_SANDBOX": str(_sandbox_root()),
        "ATLAS_CONTEXT": os.environ.get("ATLAS_CONTEXT", "on"),
        "ATLAS_ARCHIVE_AGE_DAYS": os.environ.get("ATLAS_ARCHIVE_AGE_DAYS", "7"),
    }

    return {
        "backend": backend_info,
        "retry_pricing": retry_pricing,
        "storage": storage,
        "warnings": warnings,
    }


def _cmd_doctor(args: argparse.Namespace) -> int:
    """SPEC 021 + 021.1 + 021.2: env sağlık özeti (read-only, exit 0).

    `--json` bayrağı verilirse tek satır JSON; yoksa insan-okunur.
    `--ping` bayrağı Anthropic'e minimum request atar, latency+cost raporlar.
    """
    report = _collect_doctor_report()

    if getattr(args, "ping", False):
        ping_info = _run_anthropic_ping(report["warnings"])
        if ping_info is not None:
            report["ping"] = ping_info

    if getattr(args, "json", False):
        import json as _json
        print(_json.dumps(report, ensure_ascii=False))
        return 0

    warnings = report["warnings"]
    backend_info = report["backend"]
    retry_pricing = report["retry_pricing"]
    storage = report["storage"]

    print("=== ATLAS doctor — env sağlık kontrolü ===\n")

    print("[LLM backend]")
    print(f"  ATLAS_LLM: {backend_info['ATLAS_LLM']}")
    backend = backend_info["ATLAS_LLM"]
    # Uyarılar
    for w in warnings:
        if w.startswith(("bilinmeyen backend", "claude bin", "acp agent",
                         "ANTHROPIC_API_KEY")):
            print(f"  [!] {w}")
    if backend == "claude" and "claude_bin" in backend_info:
        label = "override" if backend_info["claude_bin_source"] == "override" else "PATH"
        print(f"  claude bin ({label}): {backend_info['claude_bin']}")
    if backend == "anthropic":
        key = backend_info.get("ANTHROPIC_API_KEY", "")
        if key:
            print(f"  ANTHROPIC_API_KEY: {key}")
        print(f"  ATLAS_LLM_MODEL: {backend_info['ATLAS_LLM_MODEL']}")
        print(f"  ATLAS_LLM_ANTHROPIC_URL: {backend_info['ATLAS_LLM_ANTHROPIC_URL']}")
    if backend == "acp":
        if "acp_bin" in backend_info:
            label = "override" if backend_info["acp_bin_source"] == "override" else "PATH"
            print(f"  acp bin ({label}): {backend_info['acp_bin']}")
        if "ATLAS_LLM_ACP_ARGS" in backend_info:
            print(f"  ATLAS_LLM_ACP_ARGS: {backend_info['ATLAS_LLM_ACP_ARGS']}")
    print(f"  ATLAS_LLM_TIMEOUT: {backend_info['ATLAS_LLM_TIMEOUT']}s")

    print("\n[Retry & fiyat]")
    print(f"  ATLAS_LLM_RETRIES: {retry_pricing['ATLAS_LLM_RETRIES']} (0 = kapalı)")
    print(f"  ATLAS_LLM_BACKOFF: {retry_pricing['ATLAS_LLM_BACKOFF']}s")
    print(f"  ATLAS_LLM_JITTER: {retry_pricing['ATLAS_LLM_JITTER']}s (0 = kapalı)")
    price_in = retry_pricing["ATLAS_LLM_PRICE_IN"] or "(yok)"
    price_out = retry_pricing["ATLAS_LLM_PRICE_OUT"] or "(yok)"
    print(f"  ATLAS_LLM_PRICE_IN:  {price_in} $/M token")
    print(f"  ATLAS_LLM_PRICE_OUT: {price_out} $/M token")
    trace = retry_pricing["ATLAS_LLM_TRACE"]
    print(f"  ATLAS_LLM_TRACE: {'açık' if trace == '1' else 'kapalı'}")
    print(f"  ATLAS_LLM_OBS_CHARS: {retry_pricing['ATLAS_LLM_OBS_CHARS']}")

    print("\n[Depolama]")
    print(f"  ATLAS_VAULT: {storage['ATLAS_VAULT']}")
    print(f"  ATLAS_AUDIT: {storage['ATLAS_AUDIT']}")
    print(f"  ATLAS_SANDBOX: {storage['ATLAS_SANDBOX']}")
    print(f"  ATLAS_CONTEXT: {storage['ATLAS_CONTEXT']}")
    print(f"  ATLAS_ARCHIVE_AGE_DAYS: {storage['ATLAS_ARCHIVE_AGE_DAYS']} gün")

    # SPEC 021.2: --ping bilgisi ve yeni uyarılar
    ping = report.get("ping")
    if ping is not None:
        print("\n[Ping]")
        print(f"  latency: {ping['latency_ms']}ms")
        print(f"  input_tokens: {ping['input_tokens']}")
        print(f"  output_tokens: {ping['output_tokens']}")
        print(f"  cost_estimate: {ping['cost_estimate']}")
    # Ping uyarıları (varsa) — insan formatta [!] prefix'iyle göster
    for w in warnings:
        if w.startswith(("--ping ", "ping başarısız")):
            print(f"[!] {w}")

    return 0


def _collect_runs_from_audit(
    audit_path: Path, limit: int
) -> list[dict[str, Any]]:
    """SPEC 024: audit.jsonl'dan atlas-run oturumlarını çıkar.

    Basit heuristic: `dry_run` veya `plan` başlangıç işareti;
    sonraki `done` / `denied` / `max_steps` / `llm_error` bitiş.
    Her run için `{start_ts, end_ts, exit, steps, goal}` döner.
    """
    import json as _json
    if not audit_path.is_file():
        return []
    records: list[dict[str, Any]] = []
    try:
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("actor") == "atlas-run":
                records.append(obj)
    except OSError:
        return []

    end_actions = {"done", "denied", "max_steps", "llm_error"}
    runs: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for rec in records:
        action = rec.get("action", "")
        ts = rec.get("ts", "")
        detail = rec.get("detail", "")
        if action in ("plan", "dry_run") and current is None:
            current = {
                "start_ts": ts,
                "end_ts": ts,
                "exit": "?",
                "steps": 0,
                "goal": detail if action == "dry_run" else detail,
            }
        if current is not None:
            if action == "plan":
                current["steps"] += 1
                if not current.get("goal"):
                    current["goal"] = detail
            if action in end_actions:
                current["end_ts"] = ts
                current["exit"] = action
                if not current.get("goal"):
                    current["goal"] = detail
                runs.append(current)
                current = None
    if current is not None:
        # Bitmemiş run — açık bırak
        current["exit"] = "unfinished"
        runs.append(current)

    return runs[-limit:]


def _cost_for_run(
    run: dict[str, Any], metrics_path: Path,
    price_in: float, price_out: float,
) -> float | None:
    """SPEC 024: metrics.jsonl'dan run zaman aralığındaki cost."""
    import json as _json
    if not metrics_path.is_file():
        return None
    start = run.get("start_ts", "")
    end = run.get("end_ts", "")
    total_in = 0
    total_cc = 0
    total_cr = 0
    total_out = 0
    try:
        for line in metrics_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                m = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            if not isinstance(m, dict):
                continue
            ts = m.get("ts", "")
            # Basit string karşılaştırma — ISO 8601 kronolojik sıralı
            if start and end and (ts < start or ts > end):
                continue
            total_in += int(m.get("in", 0) or 0)
            total_out += int(m.get("out", 0) or 0)
            total_cc += int(m.get("cache_c", 0) or 0)
            total_cr += int(m.get("cache_r", 0) or 0)
    except OSError:
        return None
    if price_in <= 0 and price_out <= 0:
        return None
    return (
        total_in * price_in / 1_000_000
        + total_cc * price_in * 1.25 / 1_000_000
        + total_cr * price_in * 0.1 / 1_000_000
        + total_out * price_out / 1_000_000
    )


def _cmd_dashboard(args: argparse.Namespace) -> int:
    """SPEC 024: `.atlas/audit.jsonl` + `.atlas/metrics.jsonl` özet."""
    import json as _json

    from atlas_core.orchestrator.planner import _metrics_path

    audit_path = _audit_path()
    metrics_path = _metrics_path()
    audit = AuditLog(audit_path) if audit_path.parent.exists() else None
    chain_ok = audit.verify() if audit is not None else True

    limit: int = args.limit
    runs = _collect_runs_from_audit(audit_path, limit)
    price_in, price_out = _read_llm_prices()

    # SPEC 027: run_id eşleşmesi — .atlas/runs/*.yaml stem'lerini
    # mtime desc sırayla runs listesiyle hizala.
    runs_dir = _runs_dir()
    run_ids: list[str] = []
    if runs_dir.is_dir():
        yaml_files = sorted(
            runs_dir.glob("*.yaml"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        run_ids = [p.stem for p in yaml_files[:len(runs)]]

    if args.json:
        out_runs: list[dict[str, Any]] = []
        for i, r in enumerate(runs):
            cost = _cost_for_run(r, metrics_path, price_in, price_out)
            item = dict(r)
            item["cost"] = f"${cost:.6f}" if cost is not None else "?"
            if i < len(run_ids):
                item["run_id"] = run_ids[i]
            out_runs.append(item)
        print(_json.dumps({
            "audit_chain_valid": chain_ok,
            "runs": out_runs,
        }, ensure_ascii=False))
        return 0

    print(f"denetim zinciri: {'GEÇERLİ' if chain_ok else 'BOZULMUŞ'}")
    print(f"\n=== ATLAS dashboard — son {limit} run ===\n")
    if not runs:
        print("  (0 run)")
        return 0
    print(
        f"  {'#':<3} {'ts':<20} {'exit':<12} "
        f"{'steps':<6} {'run_id':<24} cost"
    )
    for i, r in enumerate(runs, 1):
        cost = _cost_for_run(r, metrics_path, price_in, price_out)
        cost_str = f"${cost:.6f}" if cost is not None else "?"
        ts_short = str(r.get("start_ts", ""))[:19].replace("T", " ")
        run_id = run_ids[i - 1] if (i - 1) < len(run_ids) else "-"
        print(
            f"  {i:<3} {ts_short:<20} "
            f"{r.get('exit', '?'):<12} {r.get('steps', 0):<6} "
            f"{run_id[:24]:<24} {cost_str}"
        )
    return 0


def _cmd_metrics(args: argparse.Namespace) -> int:
    """SPEC 023 + 029: `.atlas/metrics.jsonl` son N kaydı özetler.

    SPEC 029: `--alert PCT` verilmişse cache-hit oranı PCT altında
    kalırsa stderr'e `UYARI` basılır ve exit 8 döner.
    """
    import json as _json

    from atlas_core.orchestrator.planner import _metrics_path

    # SPEC 029: sınır kontrolü — geçersiz eşik = SPEC HATASI
    alert: float | None = getattr(args, "alert", None)
    if alert is not None and (alert < 0.0 or alert > 100.0):
        print(
            f"SPEC HATASI: --alert 0–100 aralığında olmalı: {alert}",
            file=sys.stderr,
        )
        return 2

    path = _metrics_path()
    limit: int = args.limit
    records: list[dict[str, Any]] = []
    if path.is_file():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = _json.loads(line)
                except _json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    records.append(obj)
        except OSError:
            pass
    tail = records[-limit:]

    total_in = sum(int(r.get("in", 0) or 0) for r in tail)
    total_out = sum(int(r.get("out", 0) or 0) for r in tail)
    total_cc = sum(int(r.get("cache_c", 0) or 0) for r in tail)
    total_cr = sum(int(r.get("cache_r", 0) or 0) for r in tail)
    # cache-hit oranı: cache_r / (in + cache_c + cache_r)
    denom = total_in + total_cc + total_cr
    hit_ratio = (total_cr / denom * 100) if denom else 0.0

    if args.json:
        print(_json.dumps(tail, ensure_ascii=False))
    else:
        print(f"=== ATLAS metrics — son {limit} çağrı ===")
        print(f"  toplam: {len(tail)} çağrı")
        print(f"  input tokens:   {total_in}")
        print(f"  output tokens:  {total_out}")
        print(f"  cache creation: {total_cc}")
        print(f"  cache read:     {total_cr}")
        print(f"  cache-hit oranı: {hit_ratio:.1f}% ({total_cr} / {denom})")
        # Cost hesabı için env'den fiyat oku
        price_in, price_out = _read_llm_prices()
        if price_in > 0 or price_out > 0:
            cost = (
                total_in * price_in / 1_000_000
                + total_cc * price_in * 1.25 / 1_000_000
                + total_cr * price_in * 0.1 / 1_000_000
                + total_out * price_out / 1_000_000
            )
            print(f"  tahmini cost:   ${cost:.6f}")
        else:
            print("  tahmini cost:   (fiyat env'i yok)")

    # SPEC 029: alarm — eşik altı → stderr UYARI + exit 8
    # --alert 0 alarmı kapatır (0 < 0 asla doğru değil).
    if alert is not None and alert > 0.0 and hit_ratio < alert:
        print(
            f"UYARI: cache-hit %{hit_ratio:.1f} < eşik %{alert:.1f}",
            file=sys.stderr,
        )
        return 8

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
    # SPEC 022: `.env` otomatik yükleme (proje kökü veya ATLAS_DOTENV).
    # Shell env override etmez; yalnız eksik değişkenleri doldurur.
    dotenv_path = os.environ.get("ATLAS_DOTENV", "").strip()
    if dotenv_path:
        _load_dotenv(Path(dotenv_path))
    else:
        _load_dotenv(Path.cwd() / ".env")

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
    p_run.add_argument("--dry-run", action="store_true",
                       help="planner çalıştır, action stub (yıkıcı iş yok) — SPEC 020")
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
    p_arc.add_argument("task", nargs="?", default=None,
                       help="pipeline/tasks/ altındaki klasör adı (--all yoksa zorunlu)")
    p_arc.add_argument("--all", action="store_true",
                       help="09-ship.md dosyası olan tüm görevleri sıraya al (SPEC 012)")
    p_arc.add_argument("--auto", action="store_true",
                       help="--all ile birlikte: yalnız ATLAS_ARCHIVE_AGE_DAYS "
                            "(varsayılan 7) günden eski ship.md'li görevler (SPEC 017)")
    p_arc.add_argument("--yes", action="store_true",
                       help="--all --apply için ikinci onay (çift kapı)")
    p_arc.add_argument("--apply", action="store_true",
                       help="dry-run yerine gerçek taşımayı çalıştır (yıkıcı)")
    p_arc.add_argument("--summary", default=None,
                       help="vault notunun gövdesi (yoksa 09-ship.md okunur)")
    p_arc.add_argument("--tasks-root", default="pipeline/tasks",
                       help="görevlerin bulunduğu kök dizin")
    p_arc.add_argument("--archive-root", default="archive",
                       help="tar.gz'lerin yazılacağı kök dizin")
    p_arc.set_defaults(func=_cmd_archive)

    p_dash = sub.add_parser("dashboard", help="Son N run özeti (SPEC 024)")
    p_dash.add_argument("--limit", type=int, default=10)
    p_dash.add_argument("--json", action="store_true")
    p_dash.set_defaults(func=_cmd_dashboard)

    p_rep = sub.add_parser("replay",
                           help="Bir run'ı yeniden çalıştır ya da listele (SPEC 027/028)")
    p_rep.add_argument("run_id", nargs="?", default=None,
                       help="run-id (`.atlas/runs/<id>.yaml`); --list ile birlikte gereksiz")
    p_rep.add_argument("--new-run-id", default=None,
                       help="replay'in yeni run-id'si (varsayılan yeni timestamp)")
    p_rep.add_argument("--dry-run", action="store_true")
    p_rep.add_argument("--list", action="store_true",
                       help="SPEC 028: kayıtlı run'ları mtime desc sırayla listele")
    p_rep.add_argument("--json", action="store_true",
                       help="SPEC 028: --list JSON çıktısı")
    p_rep.add_argument("--limit", type=int, default=20,
                       help="SPEC 028: --list son N kaydı verir (varsayılan 20)")
    p_rep.set_defaults(func=_cmd_replay)

    p_met = sub.add_parser("metrics",
                           help="LLM çağrı metrikleri özeti (SPEC 023/029)")
    p_met.add_argument("--limit", type=int, default=20,
                       help="son N kaydı özetle (varsayılan 20)")
    p_met.add_argument("--json", action="store_true",
                       help="JSON liste çıktısı")
    p_met.add_argument("--alert", type=float, default=None,
                       help="SPEC 029: cache-hit oranı bu %'den düşükse "
                            "stderr UYARI + exit 8 (0 kapatır)")
    p_met.set_defaults(func=_cmd_metrics)

    p_doc = sub.add_parser("doctor", help="Env sağlık özeti (SPEC 021)")
    p_doc.add_argument("--json", action="store_true",
                       help="JSON çıktı (CI/pre-flight uyumlu) — SPEC 021.1")
    p_doc.add_argument("--ping", action="store_true",
                       help="Anthropic'e minimum request at, latency+cost raporla — SPEC 021.2")
    p_doc.set_defaults(func=_cmd_doctor)

    args = parser.parse_args(argv)
    # Windows konsolu (cp1254) Türkçe/üstsimge çıktıyı bozabilir; UTF-8'e sabitle.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

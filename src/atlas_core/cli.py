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


def _mask_secret(value: str, keep_prefix: int = 3, keep_suffix: int = 3) -> str:
    """API key maskele: `sk-...***abc`."""
    if not value:
        return "(yok)"
    if len(value) <= keep_prefix + keep_suffix:
        return "***"
    return f"{value[:keep_prefix]}***{value[-keep_suffix:]}"


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
    """SPEC 021 + 021.1: env sağlık özeti (read-only, exit 0).

    `--json` bayrağı verilirse tek satır JSON; yoksa insan-okunur
    üç bölüm.
    """
    report = _collect_doctor_report()

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

    p_doc = sub.add_parser("doctor", help="Env sağlık özeti (SPEC 021)")
    p_doc.add_argument("--json", action="store_true",
                       help="JSON çıktı (CI/pre-flight uyumlu) — SPEC 021.1")
    p_doc.set_defaults(func=_cmd_doctor)

    args = parser.parse_args(argv)
    # Windows konsolu (cp1254) Türkçe/üstsimge çıktıyı bozabilir; UTF-8'e sabitle.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

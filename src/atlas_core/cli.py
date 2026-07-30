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
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import date, datetime
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


class _ThreadCaptureStream:
    """SPEC 031: Thread-local stdout/stderr yakalayıcı.

    `contextlib.redirect_stdout` PROCESS-GLOBAL'dir — thread-safe değil.
    Bu sınıf her thread için ayrı `StringIO` tutar; TLS'de buf yoksa
    gerçek stream'e yazar (ana thread + non-batch print'ler etkilenmez).

    Kullanım:
        cap = _ThreadCaptureStream(sys.stdout)
        sys.stdout = cap
        # Worker thread:
        cap.begin()      # TLS StringIO oluşturur
        print("x")       # → StringIO
        text = cap.end() # → "x\n", TLS buf temizlenir
        # Ana thread aynı anda print("y") → gerçek stdout ("y")
    """

    def __init__(self, real: Any) -> None:
        import threading

        self._real = real
        self._tls = threading.local()

    def begin(self) -> None:
        import io as _io

        self._tls.buf = _io.StringIO()

    def end(self) -> str:
        buf = getattr(self._tls, "buf", None)
        if buf is None:
            return ""
        val: str = str(buf.getvalue())
        del self._tls.buf
        return val

    def write(self, s: str) -> int:
        buf = getattr(self._tls, "buf", None)
        if buf is not None:
            return int(buf.write(s))
        return int(self._real.write(s))

    def flush(self) -> None:
        buf = getattr(self._tls, "buf", None)
        if buf is not None:
            return
        self._real.flush()

    def isatty(self) -> bool:
        return False


def _run_single_goal_captured(
    file_path: str, run_id_i: str, dry_run: bool,
    stdout_cap: _ThreadCaptureStream, stderr_cap: _ThreadCaptureStream,
) -> tuple[str, int, str, str]:
    """SPEC 031: Bir goal'ı çalıştırıp stdout+stderr'ini string olarak yakala.

    Thread-local yakalayıcı kullanılır — ana thread'in `print()` çağrıları
    ETKİLENMEZ.

    Döner: `(file_path, exit_code, run_id, captured_text)`.
    """
    stdout_cap.begin()
    stderr_cap.begin()
    goal_args = argparse.Namespace(
        goal_file=file_path,
        run_id=run_id_i,
        dry_run=dry_run,
    )
    try:
        rc = _cmd_run_goal(goal_args)
    except SystemExit as exc:
        rc = int(exc.code) if isinstance(exc.code, int) else 2
    out_text = stdout_cap.end()
    err_text = stderr_cap.end()
    combined = out_text + (err_text if err_text else "")
    return (file_path, rc, run_id_i, combined)


def _read_jobs_arg(args: argparse.Namespace) -> int:
    """SPEC 031: `--jobs N` doğrulama; geçersiz (< 1) → 0 (SPEC HATASI sinyali).

    Not: `or 1` KULLANMA — 0 truthy-değildir, hata yerine 1'e düşerdi.
    """
    jobs = getattr(args, "jobs", 1)
    if jobs is None:
        return 1
    jobs = int(jobs)
    if jobs < 1:
        return 0
    return jobs


def _cmd_run_batch(args: argparse.Namespace, files: list[str]) -> int:
    """SPEC 030 + 031: `atlas run --goal-file A B C [--jobs N]` batch.

    - `--jobs 1` (varsayılan): mevcut seri davranış (SPEC 030 bit-uyumlu):
      fail-fast varsayılan; `--continue-on-error` ile tümü çalışır.
    - `--jobs N > 1`: `ThreadPoolExecutor(max_workers=N)` paralel;
      fail-fast anlamlı değil (worker'lar zaten koşuyor), bu yüzden
      **paralel modda fail-fast KAPALI** (implicit continue-on-error).
      Worker stdout'ları capture edilir, ana thread sırayla basar
      (log satırları karışmaz).

    Sandbox çakışması: her goal `run_id_i = <base>_<i>` alır; goal
    tanımındaki `sandbox = <name>-<run_id>` deseni sayesinde her
    worker kendi alt-dizinini yazar. Path çakışması YOK (batch içi).

    LLM rate limit: `--jobs N` doğrudan inflight sınırıdır — max N
    goal (dolayısıyla max N canlı LLM çağrısı). API rate limit için
    ayrı env yok; kullanıcı N'i düşürerek kontrol eder.

    Run-id çakışma: `--run-id X` → `X_1, X_2, ...`; yoksa `<TS>_<i>`.
    Exit kodu: hepsi 0 → 0; aksi → en yüksek hata kodu.
    """
    continue_on_error = getattr(args, "continue_on_error", False)
    dry_run = getattr(args, "dry_run", False)
    jobs = _read_jobs_arg(args)
    if jobs == 0:
        print("SPEC HATASI: --jobs pozitif olmalı", file=sys.stderr)
        return 2
    base_run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")

    parallel = jobs > 1
    if parallel:
        # SPEC 031: paralel modda fail-fast'i devre dışı bırak (worker'lar
        # zaten koşuyor; erken çıkış temiz değil). Kullanıcıya bildir.
        mode = f"parallel (jobs={jobs})"
        if not continue_on_error:
            # Bilgi amaçlı — sözleşme: paralel = tümü çalışır
            continue_on_error = True
    else:
        mode = "continue-on-error" if continue_on_error else "fail-fast"

    print(f"=== ATLAS batch — {len(files)} goal ===")
    print(f"mod: {mode}{' + dry-run' if dry_run else ''}")
    print()

    results: list[tuple[str, int | None, str]] = []
    # (dosya, exit_code veya None="atlandı", run_id_or_skip_reason)

    if parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Thread-local capture stream'leri kur — ana thread etkilenmez.
        stdout_cap = _ThreadCaptureStream(sys.stdout)
        stderr_cap = _ThreadCaptureStream(sys.stderr)
        real_stdout = sys.stdout
        real_stderr = sys.stderr
        sys.stdout = stdout_cap
        sys.stderr = stderr_cap

        # Worker → tuple (file, rc, run_id, stdout)
        run_ids = [f"{base_run_id}_{i}" for i in range(1, len(files) + 1)]
        futures: dict[Any, tuple[int, str, str]] = {}
        try:
            with ThreadPoolExecutor(max_workers=jobs) as ex:
                for i, f in enumerate(files):
                    fut = ex.submit(
                        _run_single_goal_captured,
                        f, run_ids[i], dry_run, stdout_cap, stderr_cap,
                    )
                    futures[fut] = (i, f, run_ids[i])
                # Bitiş sırasına göre topla ama başlangıç sırasına göre bas
                done_by_idx: dict[int, tuple[str, int, str, str]] = {}
                for fut in as_completed(futures):
                    i, _f, _rid = futures[fut]
                    done_by_idx[i] = fut.result()
        finally:
            sys.stdout = real_stdout
            sys.stderr = real_stderr

        # Sırayla bas (deterministik log)
        for i, _f in enumerate(files):
            file_out, rc_out, rid, captured = done_by_idx[i]
            print(f"--- [{i + 1}/{len(files)}] {file_out}  (run_id={rid}) ---")
            # Worker stdout'unu blok halinde bas — satır sonu dahil
            if captured:
                sys.stdout.write(captured)
                if not captured.endswith("\n"):
                    sys.stdout.write("\n")
            results.append((file_out, rc_out, rid))
            print()
    else:
        # SPEC 030 mevcut seri döngü (bit-uyumlu)
        for i, f in enumerate(files, start=1):
            run_id_i = f"{base_run_id}_{i}"
            print(f"--- [{i}/{len(files)}] {f}  (run_id={run_id_i}) ---")
            goal_args = argparse.Namespace(
                goal_file=f,
                run_id=run_id_i,
                dry_run=dry_run,
            )
            rc = _cmd_run_goal(goal_args)
            results.append((f, rc, run_id_i))
            print()
            if rc != 0 and not continue_on_error:
                # Fail-fast: kalanları "atlandı" olarak işaretle
                for j in range(i, len(files)):
                    results.append((files[j], None, "atlandı (fail-fast)"))
                break

    # Özet tablo — hem seri hem paralel için ORTAK
    print(f"=== ATLAS batch özeti — {len(files)} goal ===")
    max_rc = 0
    for idx, (f_out, rc_val, note_out) in enumerate(results, start=1):
        stem = Path(f_out).stem
        if rc_val is None:
            print(f"  {idx}. {stem:<24} - {note_out}")
        elif rc_val == 0:
            print(f"  {idx}. {stem:<24} + done   (run_id={note_out})")
        else:
            print(f"  {idx}. {stem:<24} x exit={rc_val} (run_id={note_out})")
            if rc_val > max_rc:
                max_rc = rc_val
    print(f"batch exit: {max_rc}")
    return max_rc


def _cmd_run(args: argparse.Namespace) -> int:
    """Platformun tümünü bağlayan demo: kayıtlı ajan + bütçe + audit + P-A-O-R.

    `--goal-file A B C` verilirse SPEC 030 batch (birden fazla) veya SPEC 002
    tek görev sürücüsüne (`_cmd_run_goal`) dallanır.
    Aksi halde eski yer tutucu (echo) demo davranışı korunur (regresyon).
    """
    if args.goal_file:
        # SPEC 030: nargs='+' liste; N == 1 → mevcut tek-dosya davranışı
        # (bit-uyumlu); N > 1 → batch.
        files = list(args.goal_file)
        if len(files) == 1:
            # Tek dosya: args.goal_file'ı str'e indirge (mevcut _cmd_run_goal
            # `str(args.goal_file)` bekliyor).
            single_args = argparse.Namespace(
                goal_file=files[0],
                run_id=args.run_id,
                dry_run=getattr(args, "dry_run", False),
            )
            return _cmd_run_goal(single_args)
        return _cmd_run_batch(args, files)
    if not args.goal:
        print("kullanım: atlas run <hedef> | atlas run --goal-file <yaml>...", file=sys.stderr)
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


def _cmd_archive_restore(args: argparse.Namespace) -> int:
    """SPEC 033: `atlas archive --restore <id>` — arşivi geri aç.

    Dry-run varsayılan (yıkıcı: mevcut task klasörü olabilir → yazma
    yok, --apply zorunlu).
    Exit kodları:
      - 0: başarılı (veya dry-run)
      - 2: SPEC HATASI (task_id yok)
      - 3: çakışma (hedef zaten var)
      - 6: extract hatası (RestoreError, path traversal, I/O)
    """
    from atlas_core.memory.archive import (
        RestoreError,
        _find_archive_for_task,
        restore_task,
    )
    task_id = args.restore
    tasks_root = Path(args.tasks_root)
    archive_root = Path(args.archive_root)

    tar_path = _find_archive_for_task(archive_root, task_id)
    if tar_path is None:
        print(
            f"ARŞİV HATASI: arşiv bulunamadı: "
            f"{archive_root}/{task_id}-*.tar.gz",
            file=sys.stderr,
        )
        return 6
    restored_dir = tasks_root / task_id

    if not args.apply:
        print("[dry-run] geri yükleme planı:")
        print(f"  arşiv:  {tar_path}")
        print(f"  hedef:  {restored_dir}")
        if restored_dir.exists():
            print("  UYARI:  hedef zaten var — --apply patlar (exit 3)")
        print(f"Uygulamak için: atlas archive --restore {task_id} --apply")
        return 0

    audit = AuditLog(_audit_path())
    try:
        tar_out, restored_out = restore_task(task_id, archive_root, tasks_root)
    except RestoreError as exc:
        msg = str(exc)
        audit.record("atlas-archive", "restore-error", f"{task_id}: {msg[:180]}")
        print(f"ARŞİV HATASI: {msg}", file=sys.stderr)
        # Çakışma → exit 3; diğerleri → exit 6
        if "zaten var" in msg:
            return 3
        return 6

    audit.record("atlas-archive", "restore", task_id)
    print(f"geri yüklendi: {restored_out}")
    print(f"kaynak:        {tar_out}")
    return 0


def _cmd_archive(args: argparse.Namespace) -> int:
    """SPEC 007+012+033: `atlas archive <task> | --all | --restore <id> ...`.

    Dry-run varsayılan (yıkıcı işlem). Tekil: `--apply` yeter. Toplu:
    `--all --apply --yes` (çift onay). Geri yükleme: `--restore <id>
    [--apply]`.
    """
    if getattr(args, "restore", None):
        return _cmd_archive_restore(args)
    if getattr(args, "all", False):
        return _cmd_archive_all(args)
    if not args.task:
        print("SPEC HATASI: <task> ya da --all ya da --restore zorunlu", file=sys.stderr)
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


# ─────────────────────────────────────────────────────────────────────
# SPEC 032: Quality gate (DECISIONS drift denetimi)
# ─────────────────────────────────────────────────────────────────────

_DECISIONS_MD_DEFAULT = Path("DECISIONS.md")
_DECISIONS_DATE_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})")

# SPEC 032.4: `atlas doctor` çıktısı şema versiyonu (JSON tüketicileri
# şema değişikliğinde kırılmadan tanıyabilsin). Bump kuralları:
# - Alan ekleme → versiyon AYNI (bit-uyumlu).
# - Alan kaldırma / rename / tip değişikliği → major bump ("2", "3"...).
_DOCTOR_SCHEMA_VERSION = "1"


def _last_decision_date(path: Path) -> date | None:
    """SPEC 032: DECISIONS.md'de ilk (en yeni) `^## YYYY-MM-DD` girişini
    parse eder. Ters-kronolojik dosya sözleşmesi (en yeni üstte).
    Dosya yok veya tarih bulunamadı → None. Bozuk tarih → atla, devam.
    """
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        m = _DECISIONS_DATE_RE.match(line)
        if not m:
            continue
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            # Yıl/ay/gün mantıksal aralık dışı → sıradaki başlığa geç.
            continue
    return None


def _read_strict_drift_days_env() -> int:
    """SPEC 032: `ATLAS_STRICT_DRIFT_DAYS` (varsayılan 7).
    Parse hatası / 0 / negatif → varsayılan (018/026 fail-safe kalıbı).
    """
    raw = os.environ.get("ATLAS_STRICT_DRIFT_DAYS", "").strip()
    if not raw:
        return 7
    try:
        n = int(raw)
    except ValueError:
        return 7
    return n if n > 0 else 7


def _read_strict_entry_env() -> tuple[int, int]:
    """SPEC 032.1: `(window_days, min_entries)` — env okuma, fail-safe."""
    raw_win = os.environ.get("ATLAS_STRICT_ENTRY_WINDOW_DAYS", "").strip()
    try:
        window = int(raw_win) if raw_win else 30
    except ValueError:
        window = 30
    if window <= 0:
        window = 30
    raw_min = os.environ.get("ATLAS_STRICT_MIN_ENTRIES", "").strip()
    try:
        minimum = int(raw_min) if raw_min else 1
    except ValueError:
        minimum = 1
    if minimum < 0:
        minimum = 1
    return window, minimum


def _count_recent_decisions(
    decisions_path: Path | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """SPEC 032.1: DECISIONS.md'de son N gün içindeki entry sayısı.

    Şema: `{path, threshold_days, min_entries, count, warning}`.
    - Dosya yok → count=0 + uyarı.
    - `count < min_entries` → uyarı ("son N gün az giriş").
    """
    from datetime import timedelta

    path = decisions_path or _DECISIONS_MD_DEFAULT
    window_days, min_entries = _read_strict_entry_env()
    today_d = today or date.today()
    cutoff = today_d - timedelta(days=window_days)
    result: dict[str, Any] = {
        "path": str(path),
        "threshold_days": window_days,
        "min_entries": min_entries,
        "count": 0,
        "warning": None,
    }
    if not path.is_file():
        result["warning"] = (
            f"DECISIONS.md yok — son {window_days} günde 0 giriş"
        )
        return result
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        result["warning"] = f"DECISIONS.md okunamadı: {path}"
        return result
    count = 0
    for line in text.splitlines():
        m = _DECISIONS_DATE_RE.match(line)
        if not m:
            continue
        try:
            d = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if d >= cutoff:
            count += 1
    result["count"] = count
    if count < min_entries:
        result["warning"] = (
            f"DECISIONS son {window_days} günde {count} giriş, "
            f"minimum {min_entries}."
        )
    return result


def _check_vault_health(vault_path: Path | None = None) -> dict[str, Any]:
    """SPEC 032.1: Vault (Obsidian notlar) dizini sağlığı.

    - Dizin yok → uyarı ("vault yok").
    - Dizin var + `.md` yok → uyarı ("vault boş").
    - Dizin var + en az 1 `.md` → temiz.
    """
    path = vault_path or _vault_root()
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_dir(),
        "note_count": 0,
        "warning": None,
    }
    if not path.is_dir():
        result["warning"] = f"vault yok: {path}"
        return result
    try:
        notes = list(path.rglob("*.md"))
    except OSError as exc:
        result["warning"] = f"vault okunamadı: {exc}"
        return result
    result["note_count"] = len(notes)
    if not notes:
        result["warning"] = f"vault boş (0 not): {path}"
    return result


def _iter_scan_hits(scan_path: Path) -> list[tuple[Path, str, str]]:
    """SPEC 032.3: `scan_path` altında `scan_secrets` bulgularını topla.

    Ortak yardımcı — `_cmd_scan` ve `_check_scan_src` bunu kullanır (DRY).
    Her tuple `(dosya_yolu, sır_ismi, maskeli_değer)`. Path yoksa boş
    liste. Okuma hataları (UnicodeDecodeError, OSError) sessiz atlanır.

    Not: `Iterable` değil `list` döner — hem `_cmd_scan` (yazdırma
    sırasında `len(hits)` gerekli) hem `_check_scan_src` (total +
    unique sample) tam listeye ihtiyaç duyar; iterator tekrar
    tüketilemez.
    """
    if not scan_path.exists():
        return []
    files = [scan_path] if scan_path.is_file() else sorted(scan_path.rglob("*"))
    hits: list[tuple[Path, str, str]] = []
    for f in files:
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, masked in scan_secrets(text):
            hits.append((f, name, masked))
    return hits


def _check_scan_src(scan_path: Path | None = None) -> dict[str, Any]:
    """SPEC 032.2 + 032.3 + 038: Kaynak dizininde `scan_secrets` çalıştır.

    Şema: `{path, total, unique_hits, sample_files, warning}`.
    - `total`        → ham bulgu sayısı (bir dosyada birden çok olabilir)
    - `unique_hits`  → tekil dosya sayısı (SPEC 038; tıklanabilir hedef)
    - `sample_files` → ilk 5 unique dosya (özet)
    - `total > 0`    → uyarı gövdesi
    - Yol yoksa uyarı ("scan hedefi yok"); `unique_hits=0`.

    Bulgu döngüsü `_iter_scan_hits` yardımcısında (SPEC 032.3 DRY).
    Path varlık kontrolü burada kalır çünkü uyarı gövdesi özel.
    """
    path = scan_path or Path("src")
    result: dict[str, Any] = {
        "path": str(path),
        "total": 0,
        "unique_hits": 0,
        "sample_files": [],
        "warning": None,
    }
    if not path.exists():
        result["warning"] = f"scan hedefi yok: {path}"
        return result
    hits = _iter_scan_hits(path)
    # sample_files: ilk 5 UNIQUE dosya (bir dosyada birden çok bulgu
    # olabilir — aynı dosyayı iki kez basmasın).
    # SPEC 038: unique_hits = tam unique set'in büyüklüğü (sample_files
    # sadece ilk 5'i gösteriyor; kullanıcı toplam tekil dosya sayısına
    # ihtiyaç duyabiliyor — "unique hit" tıklanabilir birim).
    seen: set[str] = set()
    sample: list[str] = []
    for f, _name, _masked in hits:
        s = str(f)
        if s in seen:
            continue
        seen.add(s)
        if len(sample) < 5:
            sample.append(s)
    total = len(hits)
    result["total"] = total
    result["unique_hits"] = len(seen)
    result["sample_files"] = sample
    if total > 0:
        result["warning"] = (
            f"scan {total} olası sır buldu ({path}); "
            f"ilk dosya(lar): {', '.join(sample[:3])}"
        )
    return result


def _has_quality_warning(report: dict[str, Any]) -> bool:
    """SPEC 032 + 032.1: `quality.*` alanlarından birinde uyarı var mı."""
    quality = report.get("quality", {})
    if not isinstance(quality, dict):
        return False
    for value in quality.values():
        if isinstance(value, dict) and value.get("warning"):
            return True
    return False


def _check_decisions_drift(
    decisions_path: Path | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """SPEC 032: DECISIONS.md son giriş vs bugün tarih farkı.

    Döner: `{path, threshold_days, last_date, drift_days, warning}`.
    - `warning is None` → drift yok, temiz.
    - `warning: str` → uyarı gövdesi (Türkçe); `--strict` bunu exit 9'a
      çevirir.
    """
    path = decisions_path or _DECISIONS_MD_DEFAULT
    threshold_days = _read_strict_drift_days_env()
    last = _last_decision_date(path)
    today_d = today or date.today()
    result: dict[str, Any] = {
        "path": str(path),
        "threshold_days": threshold_days,
        "last_date": None,
        "drift_days": None,
        "warning": None,
    }
    if last is None:
        result["warning"] = (
            f"DECISIONS.md yok veya tarih parse edilemedi ({path})"
        )
        return result
    result["last_date"] = last.isoformat()
    drift = (today_d - last).days
    result["drift_days"] = drift
    if drift >= threshold_days:
        result["warning"] = (
            f"DECISIONS.md son giriş {drift} gün önce ({last.isoformat()}), "
            f"eşik {threshold_days} gün."
        )
    return result


def _collect_doctor_report(
    scan_src_path: Path | None = None,
) -> dict[str, Any]:
    """SPEC 021 + 021.1 + 032 + 032.2: env sağlık özetini yapılandırılmış
    dict olarak topla.

    Şema:
    ```
    {
      "backend": {...},
      "retry_pricing": {...},
      "storage": {...},
      "warnings": [str, ...],
      "quality": {
          "decisions_drift": {...},     # SPEC 032
          "entry_count": {...},          # SPEC 032.1
          "vault_health": {...},         # SPEC 032.1
          "scan_src": {...}              # SPEC 032.2 (yalnız istenirse)
      }
    }
    ```
    API key maskeli. Uyarılar warnings listesinde.

    `scan_src_path` verilirse `quality.scan_src` alanı EKLENİR;
    verilmezse alan yer almaz (bit-uyumluluk + ekstra IO maliyeti yok).
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

    # SPEC 032 + 032.1: DECISIONS.md drift + entry count + vault sağlık
    # denetimleri (her zaman raporlanır; --strict yalnız exit koduna
    # dönüştürür).
    quality: dict[str, Any] = {
        "decisions_drift": _check_decisions_drift(),
        "entry_count": _count_recent_decisions(),
        "vault_health": _check_vault_health(),
    }
    # SPEC 032.2: --scan-src opt-in — bayrak yoksa alan hiç eklenmez.
    if scan_src_path is not None:
        quality["scan_src"] = _check_scan_src(scan_src_path)

    return {
        # SPEC 032.4: şema versiyonu — JSON tüketicileri sürüm bumpu'nda
        # kırılmadan tanıyabilsin. Alan ekleme = aynı; kaldırma/rename =
        # major bump.
        "schema_version": _DOCTOR_SCHEMA_VERSION,
        "backend": backend_info,
        "retry_pricing": retry_pricing,
        "storage": storage,
        "warnings": warnings,
        "quality": quality,
    }


def _cmd_doctor(args: argparse.Namespace) -> int:
    """SPEC 021 + 021.1 + 021.2 + 032 + 032.2: env sağlık özeti + quality gate.

    `--json` bayrağı verilirse tek satır JSON; yoksa insan-okunur.
    `--ping` bayrağı Anthropic'e minimum request atar, latency+cost raporlar.
    `--strict` bayrağı DECISIONS drift uyarısı varsa exit 9 döner
    (SPEC 032). `--strict` yoksa mevcut davranış (exit 0) korunur.
    `--scan-src [PATH]` (SPEC 032.2) bayrağı verilirse `scan_secrets`
    kaynak dizinine uygulanır ve `quality.scan_src` alanı eklenir;
    bulgu varsa `--strict` altında exit 9 (tek kanal `_has_quality_warning`).
    """
    # SPEC 032.2: --scan-src bayrağı → Path; yoksa None (bit-uyumlu).
    scan_src = getattr(args, "scan_src", None)
    scan_src_path = Path(scan_src) if scan_src else None
    report = _collect_doctor_report(scan_src_path=scan_src_path)

    if getattr(args, "ping", False):
        ping_info = _run_anthropic_ping(report["warnings"])
        if ping_info is not None:
            report["ping"] = ping_info

    if getattr(args, "json", False):
        import json as _json
        # SPEC 032.5: --pretty → indent=2 (girintili JSON, CI + insan
        # hibrit tüketim). Bayrak yoksa tek satır (bit-uyumlu).
        pretty = getattr(args, "pretty", False)
        indent = 2 if pretty else None
        print(_json.dumps(report, ensure_ascii=False, indent=indent))
        # SPEC 032 + 032.1: --json + --strict → herhangi bir quality.*
        # uyarısı varsa exit 9. JSON çıktısı bası korunur (CI script'i
        # dosyaya kaydedebilir), yalnız exit kodu değişir.
        if getattr(args, "strict", False) and _has_quality_warning(report):
            return 9
        return 0

    warnings = report["warnings"]
    backend_info = report["backend"]
    retry_pricing = report["retry_pricing"]
    storage = report["storage"]

    print(f"=== ATLAS doctor — env sağlık kontrolü (şema v{_DOCTOR_SCHEMA_VERSION}) ===\n")

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

    # SPEC 032 + 032.1: [Kalite kapıları] bölümü
    quality = report.get("quality", {})
    drift = quality.get("decisions_drift", {})
    ecount = quality.get("entry_count", {})
    vhealth = quality.get("vault_health", {})
    print("\n[Kalite kapıları]")
    print(f"  DECISIONS.md: {drift.get('path', '(yok)')}")
    if drift.get("last_date"):
        print(f"  son giriş: {drift['last_date']} "
              f"({drift['drift_days']} gün önce, "
              f"eşik {drift['threshold_days']} gün)")
    else:
        print(f"  son giriş: (bulunamadı, eşik {drift.get('threshold_days', 7)} gün)")
    if drift.get("warning"):
        print(f"  [!] {drift['warning']}")
    # SPEC 032.1: entry count
    print(f"  son {ecount.get('threshold_days', 30)} günde giriş: "
          f"{ecount.get('count', 0)} (min {ecount.get('min_entries', 1)})")
    if ecount.get("warning"):
        print(f"  [!] {ecount['warning']}")
    # SPEC 032.1: vault health
    print(f"  vault: {vhealth.get('path', '(yok)')} "
          f"({vhealth.get('note_count', 0)} not)")
    if vhealth.get("warning"):
        print(f"  [!] {vhealth['warning']}")
    # SPEC 032.2 + 038: scan_src (opsiyonel, yalnız --scan-src verildiyse)
    # unique_hits = tekil dosya sayısı; total = ham bulgu (dosyalar
    # arasında toplam) — ikisi de raporlanır.
    scan_info = quality.get("scan_src")
    if scan_info is not None:
        total = scan_info.get("total", 0)
        unique = scan_info.get("unique_hits", 0)
        print(f"  sır taraması: {scan_info.get('path', '(yok)')} "
              f"({total} bulgu, {unique} tekil dosya)")
        if scan_info.get("warning"):
            print(f"  [!] {scan_info['warning']}")

    # SPEC 032 + 032.1 + 032.2: --strict → herhangi bir quality.* uyarısı varsa exit 9
    if getattr(args, "strict", False) and _has_quality_warning(report):
        return 9

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
    """`atlas scan <path>` — sır taraması (bağımsız komut).

    SPEC 032.3: bulgu döngüsü `_iter_scan_hits` yardımcısında (DRY,
    `_check_scan_src` ile ortak). Çıktı sözleşmesi (stdout satırları
    + stderr uyarı + exit kodu 0/1) BİREBİR korunur.
    """
    hits = _iter_scan_hits(Path(args.path))
    for f, name, masked in hits:
        print(f"{f}: {name} -> {masked}")
    total = len(hits)
    if total:
        print(f"\n{total} olası sır bulundu — commit DURDURULMALI.", file=sys.stderr)
        return 1
    print("Sır bulunamadı.")
    return 0


# ─────────────────────────────────────────────────────────────────────
# SPEC 034: pre-commit hook install/uninstall/status
# ─────────────────────────────────────────────────────────────────────

_HOOK_SIGNATURE = "# atlas-hook v1"
_HOOK_TEMPLATE_PATH = Path("tools/hooks/pre-commit")
_HOOK_TARGET_REL = Path(".git/hooks/pre-commit")


def _find_hook_shell() -> str | None:
    """SPEC 034.1: Hook için sh yolunu bul.

    - Non-Windows: her zaman `"sh"` (POSIX standart, path arama gereksiz).
    - Windows: `sh.exe` PATH'te ya da Git for Windows klasik yollarında
      veya depo-yerel `tools/git/usr/bin/sh.exe` (memory 2026-07-28
      taşınabilir kurulum). Bulunamazsa None.

    Depo-yerel ÖNCE — proje-içi taşınabilir kurulum kullanıcı home'unu
    kirletmez ve makine-özel yollarını görmezden gelmez.
    """
    import shutil as _shutil

    if sys.platform != "win32":
        return "sh"

    # Depo-yerel taşınabilir git (2026-07-28 kalıbı)
    portable = Path("tools/git/usr/bin/sh.exe")
    if portable.is_file():
        return str(portable.resolve())

    # PATH taraması
    for name in ("sh", "sh.exe"):
        found = _shutil.which(name)
        if found:
            return found

    # Klasik Git for Windows kurulum yolları
    candidates = [
        os.environ.get("ProgramFiles", ""),
        os.environ.get("ProgramFiles(x86)", ""),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    for base in candidates:
        if not base:
            continue
        for tail in (r"Git\usr\bin\sh.exe", r"Programs\Git\usr\bin\sh.exe"):
            p = Path(base) / tail
            if p.is_file():
                return str(p.resolve())

    return None


def _hook_template_text() -> str | None:
    """SPEC 034: `tools/hooks/pre-commit` şablon metnini oku.

    Yoksa None döner (fail-safe; test tarafında monkeypatch edilir).
    """
    if not _HOOK_TEMPLATE_PATH.is_file():
        return None
    try:
        return _HOOK_TEMPLATE_PATH.read_text(encoding="utf-8")
    except OSError:
        return None


def _is_atlas_hook(text: str) -> bool:
    """SPEC 034: script'in ilk 5 satırında `# atlas-hook` imzası var mı."""
    for line in text.splitlines()[:5]:
        if _HOOK_SIGNATURE.split(" v")[0] in line:
            return True
    return False


def _resolve_hook_target(cwd: Path | None = None) -> Path | None:
    """SPEC 034: `.git/hooks/pre-commit` mutlak yolunu döner.

    `.git` yoksa None (repo değil).
    """
    base = cwd or Path.cwd()
    git_dir = base / ".git"
    if not git_dir.is_dir():
        return None
    return git_dir / "hooks" / "pre-commit"


def _cmd_hooks_install(args: argparse.Namespace) -> int:
    """SPEC 034: `.git/hooks/pre-commit`'e ATLAS shim'ini kur.

    - Mevcut ATLAS shim varsa idempotent (exit 0).
    - Yabancı hook varsa `--force` yoksa exit 2 SPEC HATASI.
    - `.git` yoksa exit 2 SPEC HATASI.
    """
    template = _hook_template_text()
    if template is None:
        print(
            f"SPEC HATASI: hook şablonu bulunamadı ({_HOOK_TEMPLATE_PATH})",
            file=sys.stderr,
        )
        return 2

    target = _resolve_hook_target()
    if target is None:
        print(
            "SPEC HATASI: .git dizini yok — git repo değil",
            file=sys.stderr,
        )
        return 2

    force = getattr(args, "force", False)
    if target.is_file():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if _is_atlas_hook(existing):
            # İçerik aynıysa no-op; farklıysa güncelle (ATLAS shim'lerinde
            # sürüm farkı = güncelleme).
            if existing == template:
                print(f"hooks: {target} zaten güncel (no-op)")
                return 0
        elif not force:
            print(
                f"SPEC HATASI: {target} mevcut ve ATLAS shim'i değil; "
                "üzerine yazmak için --force kullan",
                file=sys.stderr,
            )
            return 2

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template, encoding="utf-8", newline="\n")
    # Unix'te executable bit
    try:
        import stat as _stat

        st = target.stat()
        target.chmod(st.st_mode | _stat.S_IXUSR | _stat.S_IXGRP | _stat.S_IXOTH)
    except OSError:
        pass
    print(f"hooks: kuruldu -> {target}")

    # SPEC 034.1: Windows'ta sh.exe yoksa install BAŞARILI ama uyarı
    if _find_hook_shell() is None:
        print(
            "[!] Windows'ta sh.exe bulunamadı — hook çalıştırılamaz. "
            "Git for Windows kurun (git-bash) veya tools/git/usr/bin/sh.exe "
            "ile taşınabilir git ekleyin.",
            file=sys.stderr,
        )
    return 0


def _cmd_hooks_uninstall(_args: argparse.Namespace) -> int:
    """SPEC 034: ATLAS shim'ini kaldır.

    - Yalnız ATLAS shim'i (imza doğrulama) silinir — kullanıcının kendi
      hook'una dokunulmaz.
    - Hook yoksa no-op (idempotent).
    - `.git` yoksa exit 2.
    """
    target = _resolve_hook_target()
    if target is None:
        print(
            "SPEC HATASI: .git dizini yok — git repo değil",
            file=sys.stderr,
        )
        return 2
    if not target.is_file():
        print(f"hooks: {target} yok (no-op)")
        return 0
    text = target.read_text(encoding="utf-8", errors="replace")
    if not _is_atlas_hook(text):
        print(
            f"hooks: {target} ATLAS shim'i değil (imza yok) — dokunulmadı",
            file=sys.stderr,
        )
        return 2
    target.unlink()
    print(f"hooks: kaldırıldı -> {target}")
    return 0


def _cmd_hooks_status(args: argparse.Namespace) -> int:
    """SPEC 034 + 034.1: hook durumu (kurulu mu, imza, şablonla eş mi,
    shell bulunuyor mu)."""
    import json as _json

    target = _resolve_hook_target()
    template = _hook_template_text()
    shell = _find_hook_shell()
    result: dict[str, Any] = {
        "template_path": str(_HOOK_TEMPLATE_PATH),
        "template_present": template is not None,
        "target_path": str(target) if target else None,
        "target_present": target.is_file() if target else False,
        "target_is_atlas": False,
        "target_up_to_date": False,
        # SPEC 034.1: sh guard
        "shell_available": shell is not None,
        "shell_path": shell,
    }
    if target and target.is_file():
        text = target.read_text(encoding="utf-8", errors="replace")
        result["target_is_atlas"] = _is_atlas_hook(text)
        if template is not None:
            result["target_up_to_date"] = text == template

    if getattr(args, "json", False):
        print(_json.dumps(result, ensure_ascii=False))
        return 0

    print("=== ATLAS hooks — durum ===")
    print(f"  şablon: {result['template_path']} "
          f"({'var' if result['template_present'] else 'YOK'})")
    if target is None:
        print("  hedef: (.git yok — repo değil)")
    else:
        print(f"  hedef: {result['target_path']}")
        if not result["target_present"]:
            print("    durum: kurulu değil")
        elif not result["target_is_atlas"]:
            print("    durum: kurulu (ATLAS shim'i DEĞİL)")
        elif result["target_up_to_date"]:
            print("    durum: kurulu (ATLAS shim'i, güncel)")
        else:
            print("    durum: kurulu (ATLAS shim'i, ŞABLONLA UYUŞMUYOR — "
                  "`atlas hooks install` ile güncelle)")
    # SPEC 034.1: shell tanısı
    if shell is None:
        print("  shell: YOK — Windows'ta sh.exe bulunamadı (git-bash yok)")
    else:
        print(f"  shell: {shell}")
    return 0


# ─────────────────────────────────────────────────────────────────────
# SPEC 037: `atlas ai-cli diff-summary` — package-lock diff → commit msg
# ─────────────────────────────────────────────────────────────────────

_AI_CLI_PACKAGE_LOCK = Path("tools/ai-cli/package-lock.json")


def _run_git_diff_package_lock() -> tuple[str, str | None]:
    """SPEC 037: `git diff --unified=0 tools/ai-cli/package-lock.json` çalıştır.

    Döner: `(stdout, error)`. Hata varsa `error` doldu; `stdout` boş
    olabilir. Git yoksa / repo değil / dosya yok → error dolu.
    """
    if not _AI_CLI_PACKAGE_LOCK.is_file():
        return "", f"dosya yok: {_AI_CLI_PACKAGE_LOCK}"
    try:
        proc = subprocess.run(  # noqa: S603 - sabit argv
            ["git", "diff", "--unified=0", str(_AI_CLI_PACKAGE_LOCK)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", f"git çağrısı başarısız: {exc}"
    if proc.returncode != 0:
        return "", f"git exit={proc.returncode}: {(proc.stderr or '').strip()[:200]}"
    return proc.stdout or "", None


def _parse_package_lock_diff(diff_text: str) -> list[tuple[str, str, str]]:
    """SPEC 037: package-lock diff'inden `(paket, eski, yeni)` bumpları çıkar.

    Basit heuristik: `-        "version": "X"` ve `+        "version": "Y"`
    çifti; en yakın önceki `"name": "..."` satırı paket adını verir.

    Yalnızca `AUTO_AGENTS` (opencode/kilo/cline/kimi) benzeri **tanıdık
    üst-seviye paketler**  ile filtreleme YAPILMAZ — package-lock'ta
    "opencode-ai" gibi npm paket adları görünür; bağımlıklar da bump
    olabilir. Kullanıcı commit mesajında hepsini görsün.
    """
    lines = diff_text.splitlines()
    bumps: list[tuple[str, str, str]] = []
    version_re = re.compile(r'^([-+])\s*"version":\s*"([^"]+)"')
    name_re = re.compile(r'^\s*"([^"]+)":\s*\{')

    # Her `-version + version` çifti için, en son gördüğümüz "name":
    last_name: str | None = None
    pending_old: str | None = None
    for line in lines:
        # Yeni bir paket bloğu başlıyor (name satırı) — hem `-` hem `+`
        # hem contextte olabilir. Sadece isim yakala.
        stripped = line[1:] if line[:1] in "-+ " else line
        m_name = name_re.match(stripped)
        if m_name:
            last_name = m_name.group(1)
        m_ver = version_re.match(line)
        if not m_ver:
            continue
        sign, ver = m_ver.group(1), m_ver.group(2)
        if sign == "-":
            pending_old = ver
        elif sign == "+" and pending_old is not None:
            pkg = last_name or "(bilinmeyen)"
            # package-lock'ta anahtar `node_modules/<paket>` şeklinde;
            # commit mesajı için sade paket adı istiyoruz.
            if pkg.startswith("node_modules/"):
                pkg = pkg[len("node_modules/"):]
            bumps.append((pkg, pending_old, ver))
            pending_old = None
    return bumps


def _format_bumps(bumps: list[tuple[str, str, str]]) -> str:
    """SPEC 037: bump listesini commit mesaj biçimine çevir."""
    if not bumps:
        return "(diff yok)"
    parts = [f"{pkg} {old} → {new}" for pkg, old, new in bumps]
    return "chore(ai-cli): " + "; ".join(parts)


def _cmd_ai_cli_diff_summary(_args: argparse.Namespace) -> int:
    """SPEC 037: `atlas ai-cli diff-summary` — package-lock bumpları özet."""
    diff_text, err = _run_git_diff_package_lock()
    if err is not None:
        print(f"(diff okunamadı: {err})")
        return 0
    bumps = _parse_package_lock_diff(diff_text)
    print(_format_bumps(bumps))
    return 0


# ─────────────────────────────────────────────────────────────────────
# SPEC 037.1: `atlas ai-cli update` — portable npm wrap
# ─────────────────────────────────────────────────────────────────────

_AI_CLI_DIR = Path("tools/ai-cli")
_PORTABLE_NPM_WIN = Path("tools/node/npm.cmd")
_PORTABLE_NPM_UNIX = Path("tools/node/npm")


def _find_npm_bin() -> tuple[str | None, str]:
    """SPEC 037.1: npm çalıştırılabilirini bul.

    Öncelik sırası:
      1. `tools/node/npm.cmd` (Windows portable)
      2. `tools/node/npm` (Unix portable)
      3. `shutil.which("npm")` (sistem PATH)

    Döner: `(path, source)` — source: "portable" | "path" | "".
    Bulunamazsa `(None, "")`.
    """
    import shutil as _shutil

    if sys.platform == "win32" and _PORTABLE_NPM_WIN.is_file():
        return str(_PORTABLE_NPM_WIN.resolve()), "portable"
    if _PORTABLE_NPM_UNIX.is_file():
        return str(_PORTABLE_NPM_UNIX.resolve()), "portable"
    found = _shutil.which("npm")
    if found:
        return found, "path"
    return None, ""


def _run_npm_update(npm_bin: str, dry_run: bool) -> tuple[int, str, str]:
    """SPEC 037.1: `npm update` veya `npm outdated` çağır.

    Dry-run → `npm outdated --long` (exit 0 veya 1; 1 = güncellemesi
    olan paket var, hata değil). Uygula → `npm update`.
    `cwd = tools/ai-cli` sabit.

    Döner: `(returncode, stdout, stderr)`. Subprocess hatası → (-1, "", err).
    """
    args = [npm_bin, "outdated", "--long"] if dry_run else [npm_bin, "update"]
    try:
        proc = subprocess.run(  # noqa: S603 - argv sabit + npm_bin filtrelendi
            args,
            cwd=str(_AI_CLI_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, "", f"npm çağrısı başarısız: {exc}"
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _read_ai_cli_package_json() -> tuple[dict[str, Any] | None, str | None]:
    """SPEC 037.2: `tools/ai-cli/package.json` oku, dict + err döner.

    Hata durumu (dosya yok, JSON bozuk) → `(None, err_message)`.
    """
    import json as _json

    pkg = _AI_CLI_DIR / "package.json"
    if not pkg.is_file():
        return None, f"package.json yok: {pkg}"
    try:
        text = pkg.read_text(encoding="utf-8")
        data = _json.loads(text)
    except (OSError, _json.JSONDecodeError) as exc:
        return None, f"package.json okunamadı: {exc}"
    if not isinstance(data, dict):
        return None, "package.json kök obje değil"
    return data, None


def _read_installed_version(package_name: str) -> str | None:
    """SPEC 037.2: `tools/ai-cli/node_modules/<name>/package.json` version.

    Bulunamazsa `None` (kurulu değil).
    """
    import json as _json

    pkg_dir = _AI_CLI_DIR / "node_modules" / package_name
    pkg = pkg_dir / "package.json"
    if not pkg.is_file():
        return None
    try:
        data = _json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError):
        return None
    v = data.get("version") if isinstance(data, dict) else None
    return v if isinstance(v, str) else None


def _cmd_ai_cli_list(args: argparse.Namespace) -> int:
    """SPEC 037.2: `atlas ai-cli list [--json]` — kurulu AI CLI'ları listele.

    `tools/ai-cli/package.json` dependencies alanını kaynak alır; her
    paketin `node_modules/<name>/package.json` version'ını yükler.
    Beklenen sürüm (dependencies değeri) vs kurulu sürüm karşılaştırması.

    Şema (JSON):
    ```
    {
      "path": "tools/ai-cli",
      "packages": [
        {"name": "opencode-ai", "expected": "^1.18.8", "installed": "1.18.9"},
        ...
      ]
    }
    ```
    `installed=null` → paket kurulu değil.
    Exit 0 her zaman (bilgi komutu). `tools/ai-cli/` yoksa exit 2.
    """
    import json as _json

    if not _AI_CLI_DIR.is_dir():
        print(
            f"SPEC HATASI: {_AI_CLI_DIR} yok — portable ai-cli kurulumu bulunamadı",
            file=sys.stderr,
        )
        return 2
    data, err = _read_ai_cli_package_json()
    if err is not None:
        print(f"SPEC HATASI: {err}", file=sys.stderr)
        return 2
    assert data is not None  # mypy narrow

    deps = data.get("dependencies", {}) if isinstance(data, dict) else {}
    if not isinstance(deps, dict):
        deps = {}

    packages: list[dict[str, Any]] = []
    for name in sorted(deps.keys()):
        expected = str(deps[name])
        installed = _read_installed_version(name)
        packages.append({
            "name": name,
            "expected": expected,
            "installed": installed,
        })

    if getattr(args, "json", False):
        print(_json.dumps(
            {"path": str(_AI_CLI_DIR), "packages": packages},
            ensure_ascii=False,
        ))
        return 0

    print(f"=== ATLAS ai-cli — kurulu paketler ({_AI_CLI_DIR}) ===")
    if not packages:
        print("  (paket yok)")
        return 0
    # Sütun genişliği: ad max(20, en uzun paket)
    name_w = max(20, *(len(p["name"]) for p in packages))
    for p in packages:
        ins = p["installed"] if p["installed"] is not None else "(kurulu değil)"
        print(f"  {p['name']:<{name_w}}  beklenen: {p['expected']:<10}  kurulu: {ins}")
    return 0


def _cmd_ai_cli_update(args: argparse.Namespace) -> int:
    """SPEC 037.1: `atlas ai-cli update [--dry-run]` — portable npm wrap.

    - `tools/node/npm.cmd` (Windows portable) veya `tools/node/npm`
      (Unix portable) tercih; yoksa sistem `npm` (PATH).
    - `cwd = tools/ai-cli`.
    - `--dry-run` → `npm outdated --long` (güncellemesi olan paketleri
      listele; exit 0 döner, npm 1 dönse bile "bulgu = hata değil").
    - Uygula → `npm update`; npm exit kodunu doğrudan yansıt.
    - npm bulunamadı → stderr uyarı + exit 2 (SPEC HATASI).
    - `tools/ai-cli/` yoksa → stderr uyarı + exit 2.
    """
    if not _AI_CLI_DIR.is_dir():
        print(
            f"SPEC HATASI: {_AI_CLI_DIR} yok — portable ai-cli kurulumu bulunamadı",
            file=sys.stderr,
        )
        return 2

    npm_bin, source = _find_npm_bin()
    if npm_bin is None:
        print(
            "SPEC HATASI: npm bulunamadı — tools/node/ portable kurulumu "
            "yapın veya npm'i PATH'e ekleyin",
            file=sys.stderr,
        )
        return 2

    dry_run = getattr(args, "dry_run", False)
    label = "npm outdated" if dry_run else "npm update"
    print(f"[ai-cli] {label} ({source}: {npm_bin})")

    rc, out, err = _run_npm_update(npm_bin, dry_run)
    if rc == -1:
        print(err, file=sys.stderr)
        return 2

    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err.strip():
        # npm bazen bilgilendirici mesajları stderr'e yazar (npm notice…)
        print(err, end="" if err.endswith("\n") else "\n", file=sys.stderr)

    # dry-run: outdated → exit 0 (bilgi); update → npm exit kodunu yansıt
    if dry_run:
        return 0
    return rc


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
    p_run.add_argument("--goal-file", nargs="+", default=None,
                       help="YAML hedef dosyası (SPEC 002); birden fazla verilirse "
                            "batch yürütme (SPEC 030)")
    p_run.add_argument("--run-id", default=None, help="sandbox alt dizini için sabit ad (test)")
    p_run.add_argument("--steps", type=int, default=3, help="echo demo: kaç ACT yeter")
    p_run.add_argument("--max-steps", type=int, default=8)
    p_run.add_argument("--budget", type=float, default=100.0)
    p_run.add_argument("--step-cost", type=float, default=10.0)
    p_run.add_argument("--dry-run", action="store_true",
                       help="planner çalıştır, action stub (yıkıcı iş yok) — SPEC 020")
    p_run.add_argument("--continue-on-error", action="store_true",
                       help="SPEC 030: batch modunda ilk hatada durma, tümünü çalıştır")
    p_run.add_argument("--jobs", type=int, default=1,
                       help="SPEC 031: batch paralellik (varsayılan 1 = seri, "
                            "bit-uyumlu). N > 1 → ThreadPool; fail-fast implicit "
                            "kapalı (worker'lar zaten koşuyor)")
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
                       help="pipeline/tasks/ altındaki klasör adı "
                            "(--all/--restore yoksa zorunlu)")
    p_arc.add_argument("--all", action="store_true",
                       help="09-ship.md dosyası olan tüm görevleri sıraya al (SPEC 012)")
    p_arc.add_argument("--auto", action="store_true",
                       help="--all ile birlikte: yalnız ATLAS_ARCHIVE_AGE_DAYS "
                            "(varsayılan 7) günden eski ship.md'li görevler (SPEC 017)")
    p_arc.add_argument("--yes", action="store_true",
                       help="--all --apply için ikinci onay (çift kapı)")
    p_arc.add_argument("--apply", action="store_true",
                       help="dry-run yerine gerçek taşımayı çalıştır (yıkıcı)")
    p_arc.add_argument("--restore", default=None, metavar="TASK_ID",
                       help="SPEC 033: <TASK_ID> arşivini pipeline/tasks/ "
                            "altına geri aç (dry-run varsayılan)")
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

    p_ai = sub.add_parser(
        "ai-cli",
        help="Taşınabilir AI CLI'ları (opencode/kilo/cline/kimi) yönetimi (SPEC 037)",
    )
    ai_sub = p_ai.add_subparsers(dest="ai_cmd", required=True)
    p_ai_ds = ai_sub.add_parser("diff-summary",
                                help="package-lock.json diff'inden commit mesajı önerisi")
    p_ai_ds.set_defaults(func=_cmd_ai_cli_diff_summary)
    p_ai_up = ai_sub.add_parser(
        "update",
        help="tools/ai-cli/ paketlerini güncelle (portable npm wrap, SPEC 037.1)",
    )
    p_ai_up.add_argument(
        "--dry-run", action="store_true",
        help="npm update yerine npm outdated çalıştır (yıkıcı işlem yok)",
    )
    p_ai_up.set_defaults(func=_cmd_ai_cli_update)
    p_ai_ls = ai_sub.add_parser(
        "list",
        help="tools/ai-cli/ kurulu paketleri + beklenen sürüm (SPEC 037.2)",
    )
    p_ai_ls.add_argument("--json", action="store_true", help="JSON çıktı")
    p_ai_ls.set_defaults(func=_cmd_ai_cli_list)

    p_hooks = sub.add_parser("hooks", help="Git pre-commit hook yönetimi (SPEC 034)")
    hooks_sub = p_hooks.add_subparsers(dest="hooks_cmd", required=True)
    p_hi = hooks_sub.add_parser("install", help="pre-commit shim kur")
    p_hi.add_argument("--force", action="store_true",
                      help="mevcut yabancı hook'u üzerine yaz")
    p_hi.set_defaults(func=_cmd_hooks_install)
    p_hu = hooks_sub.add_parser("uninstall", help="ATLAS shim'ini kaldır")
    p_hu.set_defaults(func=_cmd_hooks_uninstall)
    p_hs = hooks_sub.add_parser("status", help="Hook durumunu göster")
    p_hs.add_argument("--json", action="store_true", help="JSON çıktı")
    p_hs.set_defaults(func=_cmd_hooks_status)

    p_doc = sub.add_parser("doctor",
                           help="Env sağlık özeti + quality gate (SPEC 021/032)")
    p_doc.add_argument("--json", action="store_true",
                       help="JSON çıktı (CI/pre-flight uyumlu) — SPEC 021.1")
    p_doc.add_argument("--ping", action="store_true",
                       help="Anthropic'e minimum request at, latency+cost raporla — SPEC 021.2")
    p_doc.add_argument("--strict", action="store_true",
                       help="SPEC 032: quality.* uyarısı varsa exit 9")
    p_doc.add_argument("--scan-src", nargs="?", const="src", default=None,
                       help="SPEC 032.2: sır taramasını doctor'a dahil et "
                            "(varsayılan yol: src)")
    p_doc.add_argument("--pretty", action="store_true",
                       help="SPEC 032.5: --json ile birlikte, girintili JSON")
    p_doc.set_defaults(func=_cmd_doctor)

    args = parser.parse_args(argv)
    # Windows konsolu (cp1254) Türkçe/üstsimge çıktıyı bozabilir; UTF-8'e sabitle.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

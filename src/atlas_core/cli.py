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


def _read_metrics_avg_tokens(
    limit: int = 20,
) -> tuple[int | None, int]:
    """SPEC 072: `.atlas/metrics.jsonl` son N kaydının ortalama toplam
    token'ı (in+out+cache_c+cache_r).

    Return: `(avg_tokens_per_call, sample_count)`. Metrik yoksa veya
    < 3 kayıt → `(None, sample_count)` (adaptif hesap için yeterli
    numune yok — çağıran static fallback'e döner).
    """
    import json as _json

    from atlas_core.orchestrator.planner import _metrics_path

    path = _metrics_path()
    if not path.is_file():
        return None, 0
    records: list[dict[str, Any]] = []
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if not s:
                continue
            try:
                obj = _json.loads(s)
            except _json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                records.append(obj)
    except OSError:
        return None, 0
    tail = records[-limit:]
    n = len(tail)
    if n < 3:
        return None, n
    total = 0
    for r in tail:
        total += (
            int(r.get("in", 0) or 0)
            + int(r.get("out", 0) or 0)
            + int(r.get("cache_c", 0) or 0)
            + int(r.get("cache_r", 0) or 0)
        )
    return total // n, n


def _estimate_run_cost(
    goal_obj: Any, backend: str, tokens_per_call: int,
    price_in: float, price_out: float,
    *,
    source: str = "static",
    sample_count: int = 0,
) -> dict[str, Any]:
    """SPEC 069 + 072: Run başlamadan önden tahmini planlanan çağrı+token+cost.

    Heuristik (SPEC 069): her adım 1 planner çağrısı → `tokens_per_call`
    token (varsayılan 500). Toplam token = `max_steps * tokens_per_call`
    (input+output birleşik). Cost = tokens × (price_in+price_out) / 1M.

    Backend `stub` ise cost 0 (LLM çağrılmaz). `anthropic`/`acp` için
    env fiyatları kullanılır; fiyat 0 ise cost 0 raporlanır.

    SPEC 072: `source` alanı raporda görünür ("static" veya "adaptive-avg");
    adaptive için `sample_count` numune sayısı.
    """
    max_steps = int(goal_obj.max_steps)
    total_tokens = max_steps * tokens_per_call
    if backend == "stub" or (price_in == 0.0 and price_out == 0.0):
        cost = 0.0
    else:
        # Yaklaşım: yarısı input, yarısı output (heuristik)
        input_tok = total_tokens // 2
        output_tok = total_tokens - input_tok
        cost = (input_tok * price_in + output_tok * price_out) / 1_000_000
    return {
        "goal": goal_obj.goal,
        "backend": backend,
        "max_steps": max_steps,
        "budget": float(goal_obj.budget),
        "tokens_per_call": tokens_per_call,
        "estimated_total_tokens": total_tokens,
        "estimated_cost_usd": round(cost, 6),
        "price_in_per_1m": price_in,
        "price_out_per_1m": price_out,
        "source": source,
        "sample_count": sample_count,
    }


def _cmd_run_goal(args: argparse.Namespace) -> int:
    """SPEC 002 + 069: `--goal-file` verildiğinde gerçek görev sürücüsü.

    goal YAML'ini yükler, sandbox'i kurar, planner+action+judge'u
    fabrikadan alır, run_loop'u sürer. ActionDeniedError yakalanır,
    audit'e 'denied' kaydi düşer, exit 5.

    SPEC 006: `_context_enabled(goal)` True ise GBrain.context_for(goal.goal)
    tek kez çağrılıp planner fabrikasına geçirilir; static görevler ve
    `ATLAS_CONTEXT=off` durumu için GBrain hiç instantiate edilmez.

    SPEC 069: `--estimate` bayrağı → LLM çağrısı YAPMA, planner+context+
    action fabrikaları hiç kurulmaz. Yalnız `_estimate_run_cost` sonucu
    (JSON veya insan) basılır, exit 0. Audit yazılmaz.
    """
    try:
        goal = load_goal(Path(args.goal_file))
    except SpecError as exc:
        print(f"SPEC HATASI: {exc}", file=sys.stderr)
        return 2

    # SPEC 069: --estimate erken dallanma — LLM/context/sandbox hiç kurulmaz
    if getattr(args, "estimate", False):
        import json as _json
        backend = os.environ.get("ATLAS_LLM", "stub")
        # SPEC 072: --adaptive → metrics.jsonl son N call ortalaması.
        # Bulgu yoksa static fallback + UYARI (source raporda).
        adaptive = getattr(args, "adaptive", False)
        adaptive_n = int(getattr(args, "adaptive_n", 20))
        source = "static"
        sample_count = 0
        tokens_per_call: int
        if adaptive:
            avg, sample_count = _read_metrics_avg_tokens(adaptive_n)
            if avg is not None and avg > 0:
                tokens_per_call = avg
                source = "adaptive-avg"
            else:
                # Fallback: static (env veya 500)
                try:
                    tokens_per_call = int(
                        os.environ.get("ATLAS_ESTIMATE_TOKENS_PER_CALL", "500")
                    )
                except ValueError:
                    tokens_per_call = 500
                source = "adaptive-fallback-static"
        else:
            try:
                tokens_per_call = int(
                    os.environ.get("ATLAS_ESTIMATE_TOKENS_PER_CALL", "500")
                )
            except ValueError:
                tokens_per_call = 500
        price_in, price_out = _read_llm_prices()
        summary = _estimate_run_cost(
            goal, backend, tokens_per_call, price_in, price_out,
            source=source, sample_count=sample_count,
        )
        if getattr(args, "json", False):
            print(_json.dumps(summary, ensure_ascii=False))
        else:
            print("=== ATLAS run --estimate (LLM cagrilmadi) ===")
            print(f"  goal:            {summary['goal'][:80]}")
            print(f"  backend:         {summary['backend']}")
            print(f"  max_steps:       {summary['max_steps']}")
            print(f"  budget:          {summary['budget']}")
            print(f"  tokens/call:     {summary['tokens_per_call']}  "
                  f"(source: {summary['source']}"
                  f"{f', n={sample_count}' if sample_count else ''})")
            print(f"  tahmini token:   {summary['estimated_total_tokens']}")
            print(f"  tahmini cost:    ${summary['estimated_cost_usd']:.6f}")
            if summary["price_in_per_1m"] == 0.0 and summary["price_out_per_1m"] == 0.0:
                print("  UYARI: fiyat env yok (ATLAS_LLM_PRICE_IN_PER_1M / _OUT_)")
            if source == "adaptive-fallback-static":
                print(f"  UYARI: metrics.jsonl < 3 kayit ({sample_count}); "
                      "static fallback kullanildi")
        return 0

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


def _summarize_dry_run_captures(captures: list[str]) -> dict[str, Any]:
    """SPEC 031.1: Worker captured output'larından step agregasyonu.

    `_cmd_run_goal` her step'i `  <kind:<8s> <text[:120]>` biçiminde
    basıyor (`kind in {plan, act, observe, reflect}`). Regex ile
    sayar.

    Döner:
        {
          "total_steps": int,
          "by_kind": {"plan": N, "act": N, "observe": N, "reflect": N},
          "actions": ["write:...", "read:...", ...]   # act step text'leri
        }
    """
    step_re = re.compile(r"^\s{2}(plan|act|observe|reflect)\s+(.*)$")
    by_kind = {"plan": 0, "act": 0, "observe": 0, "reflect": 0}
    actions: list[str] = []
    total = 0
    for cap in captures:
        for raw in cap.splitlines():
            m = step_re.match(raw)
            if not m:
                continue
            kind, text = m.group(1), m.group(2).strip()
            by_kind[kind] = by_kind.get(kind, 0) + 1
            total += 1
            if kind == "act":
                actions.append(text[:80])
    return {
        "total_steps": total,
        "by_kind": by_kind,
        "actions": actions,
    }


def _print_dry_run_summary(summary: dict[str, Any]) -> None:
    """SPEC 031.1: Toplu dry-run özetini insan formatında bas."""
    by_kind = summary["by_kind"]
    kinds_str = ", ".join(
        f"{k}={by_kind[k]}" for k in ("plan", "act", "observe", "reflect")
    )
    print("=== ATLAS batch dry-run özeti ===")
    print(f"  toplam step: {summary['total_steps']} ({kinds_str})")
    if summary["actions"]:
        # İlk 5 eylem — daha uzunsa "…N daha"
        acts = summary["actions"]
        first = acts[:5]
        for a in first:
            print(f"    · {a}")
        remaining = len(acts) - len(first)
        if remaining > 0:
            print(f"    · …{remaining} eylem daha")


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
    # SPEC 031.1: dry-run modunda worker çıktılarını topla → toplu özet
    captured_outputs: list[str] = []

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
            if dry_run:
                captured_outputs.append(captured)
            print()
    else:
        # SPEC 030 mevcut seri döngü (bit-uyumlu).
        # SPEC 031.1: dry-run'da tee-capture — stdout'a real-time yazar
        # + buf'a kopyalar → toplu özet için parse edilir.
        import contextlib as _contextlib
        import io as _io

        class _Tee:
            def __init__(self, primary: Any, mirror: Any) -> None:
                self._primary = primary
                self._mirror = mirror

            def write(self, s: str) -> int:
                self._mirror.write(s)
                return int(self._primary.write(s))

            def flush(self) -> None:
                self._primary.flush()

        for i, f in enumerate(files, start=1):
            run_id_i = f"{base_run_id}_{i}"
            print(f"--- [{i}/{len(files)}] {f}  (run_id={run_id_i}) ---")
            goal_args = argparse.Namespace(
                goal_file=f,
                run_id=run_id_i,
                dry_run=dry_run,
            )
            if dry_run:
                buf = _io.StringIO()
                with _contextlib.redirect_stdout(_Tee(sys.stdout, buf)):
                    rc = _cmd_run_goal(goal_args)
                captured_outputs.append(buf.getvalue())
            else:
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

    # SPEC 031.1: dry-run toplu özeti (worker step count'ları
    # captured output'lardan regex ile agregasyon)
    if dry_run and captured_outputs:
        summary = _summarize_dry_run_captures(captured_outputs)
        if summary["total_steps"] > 0:
            print()
            _print_dry_run_summary(summary)

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
                estimate=getattr(args, "estimate", False),
                adaptive=getattr(args, "adaptive", False),
                adaptive_n=getattr(args, "adaptive_n", 20),
                json=getattr(args, "json", False),
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
    """SPEC 033 + 071: `atlas archive --restore <id>` — arşivi geri aç.

    Dry-run varsayılan (yıkıcı: mevcut task klasörü olabilir → yazma
    yok, --apply zorunlu).

    SPEC 071: `--restore --search PATTERN` verilirse `<id>` yerine
    pattern'e uyan tek arşiv otomatik bulunur. 0 eşleşme → exit 6;
    2+ eşleşme → exit 2 (belirsizlik; kullanıcı `--search` daraltmalı).

    Exit kodları:
      - 0: başarılı (veya dry-run)
      - 2: SPEC HATASI (task_id yok / --search belirsiz / regex hata)
      - 3: çakışma (hedef zaten var)
      - 6: extract hatası (RestoreError, path traversal, I/O)
    """
    from atlas_core.memory.archive import (
        RestoreError,
        _find_archive_for_task,
        restore_task,
    )
    tasks_root = Path(args.tasks_root)
    archive_root = Path(args.archive_root)

    # SPEC 071: --restore boş (`--restore --search P`) veya --restore
    # <id> + --search her ikisi de arama-tabanlı seçim yapar.
    restore_arg = args.restore  # "" (bayraksız) veya <id> string
    search_pattern = getattr(args, "search", None)

    if search_pattern:
        try:
            hits = _search_archive_contents(archive_root, search_pattern)
        except ValueError as exc:
            print(f"SPEC HATASI: {exc}", file=sys.stderr)
            return 2
        if not hits:
            print(
                f"ARŞİV HATASI: --search '{search_pattern}' hiç eşleşme "
                f"vermedi: {archive_root}",
                file=sys.stderr,
            )
            return 6
        if len(hits) > 1:
            print(
                f"SPEC HATASI: --search '{search_pattern}' {len(hits)} "
                f"arşive uyuyor; belirsiz, daralt:",
                file=sys.stderr,
            )
            for h in hits:
                print(f"  - {h['archive']}", file=sys.stderr)
            return 2
        # Tek eşleşme: <task_id>-YYYY-MM-DD.tar.gz → task_id çıkar
        archive_name = hits[0]["archive"]
        stem = archive_name[:-len(".tar.gz")]
        # `-YYYY-MM-DD` (11 karakter) kaldır
        if len(stem) > 11 and stem[-11] == "-":
            task_id = stem[:-11]
        else:
            task_id = stem
    else:
        task_id = restore_arg

    if not task_id:
        print(
            "SPEC HATASI: --restore için <task_id> veya --search gerekli",
            file=sys.stderr,
        )
        return 2

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


def _search_archive_contents(
    archive_root: Path, pattern: str,
) -> list[dict[str, Any]]:
    """SPEC 065: `<archive_root>/*.tar.gz` içinde dosya adı regex arama.

    Tar açmaz — `tarfile.open + getnames()` metadata'sı yeter.
    Return: her eşleşen tar için `{archive: <tar-adı>, matches: [str, ...]}`
    (sorted archive-adı, sorted matches; deterministik).

    Regex `re.search` (part-match); büyük/küçük harf duyarlı. Kullanıcı
    isterse `(?i)` inline flag kullanabilir.
    """
    import re
    import tarfile

    if not archive_root.is_dir():
        return []
    try:
        prog = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"regex hatası: {exc}") from exc
    results: list[dict[str, Any]] = []
    for tar_path in sorted(archive_root.glob("*.tar.gz")):
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                names = tar.getnames()
        except (OSError, tarfile.TarError):
            continue
        matched = sorted({n for n in names if prog.search(n)})
        if matched:
            results.append({
                "archive": tar_path.name,
                "matches": matched,
            })
    return results


def _list_archive_entries(archive_root: Path) -> list[dict[str, Any]]:
    """SPEC 075: `<archive_root>/*.tar.gz` metadata listesi.

    Her arşiv için `{archive, task_id, date, size_bytes, size_human,
    member_count, mtime}` — tar açılmadan (`getmembers()` metadata).
    Deterministik sıra: alfabetik.
    """
    import tarfile
    from datetime import datetime as _dt

    if not archive_root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for tar_path in sorted(archive_root.glob("*.tar.gz")):
        try:
            stat = tar_path.stat()
        except OSError:
            continue
        # <task_id>-YYYY-MM-DD.tar.gz → task_id + date
        name = tar_path.name
        stem = name[:-len(".tar.gz")]
        task_id: str
        date_str: str
        if len(stem) > 11 and stem[-11] == "-":
            task_id = stem[:-11]
            date_str = stem[-10:]  # YYYY-MM-DD
        else:
            task_id = stem
            date_str = ""
        # Member count — tar açmadan
        member_count = 0
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                member_count = len(tar.getnames())
        except (OSError, tarfile.TarError):
            member_count = -1
        size_bytes = stat.st_size
        out.append({
            "archive": name,
            "task_id": task_id,
            "date": date_str,
            "size_bytes": size_bytes,
            "size_human": _human_bytes(size_bytes),
            "member_count": member_count,
            "mtime": _dt.fromtimestamp(stat.st_mtime).isoformat(
                timespec="seconds"),
        })
    return out


def _cmd_archive_list(args: argparse.Namespace) -> int:
    """SPEC 075 + 079: `atlas archive --list [--json] [--sort-by KEY]
    [--desc]`.

    Arşiv kökündeki tar.gz dosyalarının metadata listesi. Yıkıcı iş yok.

    SPEC 079: `--sort-by {name,size,date,members}` (default `name`;
    SPEC 075 alfabetik davranış). `--desc` ters sıra.

    Exit:
      - 0: başarı (bilgi komutu)
      - 2: archive_root yok
    """
    import json as _json
    archive_root = Path(args.archive_root)
    if not archive_root.is_dir():
        print(
            f"SPEC HATASI: arşiv kökü yok: {archive_root}",
            file=sys.stderr,
        )
        return 2
    entries = _list_archive_entries(archive_root)
    # SPEC 079: sıralama
    sort_by = getattr(args, "sort_by", "name") or "name"
    desc = bool(getattr(args, "desc", False))
    key_map = {
        "name": lambda e: e["archive"].lower(),
        "size": lambda e: e["size_bytes"],
        "date": lambda e: e["date"] or e["mtime"],  # date boşsa mtime
        "members": lambda e: max(e["member_count"], 0),  # -1 → 0
    }
    if sort_by not in key_map:
        print(
            f"SPEC HATASI: --sort-by geçersiz: '{sort_by}' "
            f"(kabul: {', '.join(sorted(key_map))})",
            file=sys.stderr,
        )
        return 2
    entries = sorted(entries, key=key_map[sort_by], reverse=desc)
    if getattr(args, "json", False):
        print(_json.dumps(entries, ensure_ascii=False))
        return 0
    print(f"=== ATLAS archive --list ({archive_root}) — {len(entries)} arsiv ===")
    if not entries:
        print("  (arsiv yok)")
        return 0
    # Sütun genişliği
    tid_w = max(24, *(len(e["task_id"]) for e in entries))
    for e in entries:
        mc = e["member_count"]
        mc_str = str(mc) if mc >= 0 else "?"
        print(
            f"  {e['task_id']:<{tid_w}}  {e['date']:<12}  "
            f"{e['size_human']:>10}  {mc_str:>6} uye  {e['mtime']}"
        )
    return 0


def _cmd_archive_search(args: argparse.Namespace) -> int:
    """SPEC 065: `atlas archive --search PATTERN [--json]`.

    Archive kökündeki tüm `*.tar.gz` dosyaları içinde dosya adı (arcname)
    regex araması. Tar dosyaları AÇILMAZ — metadata yeter.

    Exit:
      - 0: arama tamam (bulgu olsa da olmasa da bilgi komutu)
      - 2: SPEC HATASI (archive_root yok / pattern regex hatası)
    """
    import json as _json
    archive_root = Path(args.archive_root)
    if not archive_root.is_dir():
        print(
            f"SPEC HATASI: arşiv kökü yok: {archive_root}",
            file=sys.stderr,
        )
        return 2
    try:
        hits = _search_archive_contents(archive_root, args.search)
    except ValueError as exc:
        print(f"SPEC HATASI: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "json", False):
        print(_json.dumps(hits, ensure_ascii=False))
        return 0

    total = sum(len(h["matches"]) for h in hits)
    print(
        f"=== ATLAS archive search — {len(hits)} arsivde {total} eslesme ==="
    )
    if not hits:
        print("  (bulgu yok)")
        return 0
    for h in hits:
        print(f"\n  {h['archive']} ({len(h['matches'])} eslesme):")
        for name in h["matches"]:
            print(f"    - {name}")
    return 0


def _cmd_archive(args: argparse.Namespace) -> int:
    """SPEC 007+012+033+065+071: `atlas archive [<task>|--all|--restore
    <id>|--search P|--restore --search P]`.

    Dry-run varsayılan (yıkıcı işlem). Tekil: `--apply` yeter. Toplu:
    `--all --apply --yes` (çift onay). Geri yükleme: `--restore <id>
    [--apply]`. Arama: `--search PATTERN [--json]` (SPEC 065).
    SPEC 071: `--restore --search PATTERN` → arama sonucu tek arşivse
    otomatik geri yükle.

    Dispatcher sırası:
      1. `--restore` (SPEC 033/071) — --search ile birlikte olabilir
      2. `--search` (SPEC 065) — list-only mod
      3. `--all` (SPEC 012)
      4. tekil task (SPEC 007)
    """
    # SPEC 075: --list (bilgi komutu, en önde çünkü read-only)
    if getattr(args, "list", False):
        return _cmd_archive_list(args)
    # SPEC 071: --restore --search PATTERN → restore-search birleşim.
    # `--restore` `nargs="?"` const="" default=None → `is not None` truthy.
    if getattr(args, "restore", None) is not None:
        return _cmd_archive_restore(args)
    if getattr(args, "search", None):
        return _cmd_archive_search(args)
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


def _build_replay_json_body(limit: int) -> str:
    """SPEC 055: `_collect_replay_runs(limit)` sonucu JSON string.

    Her istek yeniden okur (canlı liste). SPEC 028 `--list --json`
    çıktı sözleşmesiyle BİT-UYUMLU (aynı `_collect_replay_runs`).
    """
    import json as _json
    runs = _collect_replay_runs(limit)
    return _json.dumps(runs, ensure_ascii=False)


def _cmd_replay(args: argparse.Namespace) -> int:
    """SPEC 027 + 028 + 055: `atlas replay [<run-id>|--list|--serve]`.

    `--list` → mevcut run'ları listele (`_cmd_replay_list`).
    `--serve HOST:PORT` → SPEC 055: `_collect_replay_runs(limit)` sonucu
    JSON HTTP endpoint (blocking; Ctrl+C ile durdur).
    Aksi → 027 davranışı: kopyayı bulup çalıştır.
    """
    # SPEC 055: --serve HOST:PORT (blocking) — --list/--run-id ile mutex
    serve_spec = getattr(args, "serve", None)
    if serve_spec:
        from atlas_core.observability.prometheus_server import (
            parse_host_port,
            serve_prometheus_http,
        )
        if getattr(args, "list", False):
            print("SPEC HATASI: --serve ve --list birlikte kullanılamaz",
                  file=sys.stderr)
            return 2
        if args.run_id:
            print("SPEC HATASI: --serve ile birlikte run-id verilemez "
                  "(server tüm liste yayımlar)",
                  file=sys.stderr)
            return 2
        try:
            host, port = parse_host_port(serve_spec)
        except ValueError as exc:
            print(f"SPEC HATASI: {exc}", file=sys.stderr)
            return 2
        limit = int(args.limit)
        serve_prometheus_http(
            host, port,
            lambda: _build_replay_json_body(limit),
            content_type="application/json; charset=utf-8",
            allowed_paths=("/", "/runs"),
        )
        return 0

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

# SPEC 062: `atlas doctor --diff --auto-baseline` için varsayılan snapshot
# konumu. `.atlas/` git-ignored → commit döngüsü yok.
_DEFAULT_DOCTOR_BASELINE = Path(".atlas/doctor-baseline.json")

# SPEC 080: baseline tarihçesi dizini
_DEFAULT_DOCTOR_HISTORY_DIR = Path(".atlas/doctor-history")


def _list_doctor_history() -> list[dict[str, Any]]:
    """SPEC 080: `.atlas/doctor-history/baseline-*.json` metadata listesi.

    Return: her snapshot için `{path, date, size_bytes, size_human, mtime}`.
    Sıra: date desc (en yeni önce). Dosya yok → [].
    """
    from datetime import datetime as _dt
    if not _DEFAULT_DOCTOR_HISTORY_DIR.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(_DEFAULT_DOCTOR_HISTORY_DIR.glob("baseline-*.json")):
        try:
            stat = p.stat()
        except OSError:
            continue
        # `baseline-YYYY-MM-DD.json` → date
        stem = p.stem  # baseline-YYYY-MM-DD
        date_str = stem[9:] if stem.startswith("baseline-") else ""
        size = stat.st_size
        out.append({
            "path": str(p),
            "date": date_str,
            "size_bytes": size,
            "size_human": _human_bytes_or_fallback(size),
            "mtime": _dt.fromtimestamp(stat.st_mtime).isoformat(
                timespec="seconds"),
        })
    # Date desc: alfabetik ters (YYYY-MM-DD lex sıra = tarih sıra)
    out.sort(key=lambda e: e["date"], reverse=True)
    return out


def _human_bytes_or_fallback(n: int) -> str:
    """`_human_bytes` var, forward. Bulunmazsa basit fallback."""
    try:
        return _human_bytes(n)
    except NameError:
        # Forward reference — cli.py içinde _human_bytes daha sonra tanımlanmış
        if n < 1024:
            return f"{n} B"
        if n < 1024 * 1024:
            return f"{n / 1024:.1f} KB"
        return f"{n / (1024 * 1024):.1f} MB"


def _prune_doctor_history(keep: int) -> list[Path]:
    """SPEC 080: `.atlas/doctor-history/baseline-*.json` retention.

    date desc + ilk `keep` tutar; geri kalanı siler. `keep < 1` →
    ValueError. Dizin yok → [].
    """
    if keep < 1:
        raise ValueError(f"keep >= 1 olmalı: {keep}")
    if not _DEFAULT_DOCTOR_HISTORY_DIR.is_dir():
        return []
    files = sorted(
        _DEFAULT_DOCTOR_HISTORY_DIR.glob("baseline-*.json"),
        key=lambda p: p.name,  # baseline-YYYY-MM-DD alfabetik = tarih sıra
        reverse=True,
    )
    to_delete = files[keep:]
    deleted: list[Path] = []
    for p in to_delete:
        try:
            p.unlink()
            deleted.append(p)
        except OSError:
            continue
    return deleted
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


def _check_http(url: str, timeout: float = 5.0) -> dict[str, Any]:
    """SPEC 054: HTTP GET URL — sağlık kontrolü.

    - 2xx → warning=None, status_code=<code>, latency_ms=<ölçüm>
    - non-2xx → warning="HTTP <code>"
    - connect timeout / DNS / socket error → warning="<exc>", status=None
    - `URL` scheme http/https değil → warning="URL scheme geçersiz"

    Test için urllib.request'i monkeypatch et.
    """
    import time
    import urllib.error
    import urllib.request
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    if scheme not in ("http", "https"):
        return {
            "url": url,
            "status_code": None,
            "latency_ms": None,
            "warning": f"URL scheme geçersiz: '{scheme}' (http/https bekleniyor)",
        }

    req = urllib.request.Request(url, method="GET")
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            status = resp.status
            elapsed_ms = (time.perf_counter() - start) * 1000
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "url": url,
            "status_code": exc.code,
            "latency_ms": round(elapsed_ms, 2),
            "warning": f"HTTP {exc.code}",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "url": url,
            "status_code": None,
            "latency_ms": None,
            "warning": f"bağlantı hatası: {exc}",
        }

    result: dict[str, Any] = {
        "url": url,
        "status_code": status,
        "latency_ms": round(elapsed_ms, 2),
        "warning": None,
    }
    if not 200 <= status < 300:
        result["warning"] = f"HTTP {status}"
    return result


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


def _diff_doctor_reports(
    baseline: dict[str, Any], current: dict[str, Any],
) -> dict[str, Any]:
    """SPEC 057: iki `atlas doctor --json` raporu arasındaki delta.

    - `warnings_added` : current'te var, baseline'da yok.
    - `warnings_removed` : baseline'da var, current'te yok.
    - `quality_deltas` : her `quality.<field>` için:
      - `before_warning`, `after_warning` (str|None)
      - `change`: `regressed` (None→str), `resolved` (str→None),
        `changed` (str→str farklı mesaj), `unchanged` (aynı, listeye
        eklenmez), `disappeared` (baseline'da alan var current'te yok),
        `appeared` (current'te var baseline'da yok)
    - `has_regression` : yeni uyarı VEYA regressed/appeared+warning var.
    - `has_improvement` : kaldırılan uyarı VEYA resolved var.
    - `schema_version_baseline` / `schema_version_current`: değişiklik
      raporlama için.

    Deterministik: warnings sorted, quality_deltas key sorted.
    """
    b_warns = list(baseline.get("warnings", []) or [])
    c_warns = list(current.get("warnings", []) or [])
    added = sorted(set(c_warns) - set(b_warns))
    removed = sorted(set(b_warns) - set(c_warns))

    b_q = baseline.get("quality", {}) if isinstance(baseline.get("quality"), dict) else {}
    c_q = current.get("quality", {}) if isinstance(current.get("quality"), dict) else {}

    quality_deltas: dict[str, dict[str, Any]] = {}
    has_regression = bool(added)

    all_fields = sorted(set(b_q) | set(c_q))
    for field in all_fields:
        b_field = b_q.get(field)
        c_field = c_q.get(field)
        b_w = b_field.get("warning") if isinstance(b_field, dict) else None
        c_w = c_field.get("warning") if isinstance(c_field, dict) else None

        if field in b_q and field not in c_q:
            change = "disappeared"
        elif field not in b_q and field in c_q:
            change = "appeared"
            if c_w:
                has_regression = True
        elif b_w is None and c_w is not None:
            change = "regressed"
            has_regression = True
        elif b_w is not None and c_w is None:
            change = "resolved"
        elif b_w != c_w:
            change = "changed"
            # message change ile içerik farkı — regresyon olarak sayma
        else:
            continue  # unchanged — dahil etme

        quality_deltas[field] = {
            "before_warning": b_w,
            "after_warning": c_w,
            "change": change,
        }

    has_improvement = bool(removed) or any(
        d["change"] in ("resolved", "disappeared")
        for d in quality_deltas.values()
    )

    return {
        "warnings_added": added,
        "warnings_removed": removed,
        "quality_deltas": quality_deltas,
        "has_regression": has_regression,
        "has_improvement": has_improvement,
        "schema_version_baseline": baseline.get("schema_version"),
        "schema_version_current": current.get("schema_version"),
    }


def _doctor_report_to_prometheus(report: dict[str, Any]) -> str:
    """SPEC 047: doctor raporunu Prometheus text v0.0.4 formatına çevir.

    Metrikler:
      - `atlas_doctor_up` (gauge) — komut çalıştıysa 1 (Prometheus `up`
        konvansiyonu; alertmanager için canonical sinyal).
      - `atlas_doctor_warnings_total` (gauge) — `report["warnings"]` uzunluğu.
      - `atlas_doctor_quality_healthy{field=...}` (gauge) — her quality
        alanı için 0/1 (1 = warning yok). Alan yoksa satır basılmaz.
      - `atlas_doctor_scan_src_hits_total` + `_scan_src_unique_files`
        (gauge, opsiyonel) — yalnız `scan_src` alanı raporda varsa.

    Her metrik HELP + TYPE + değer satırı taşır. Çıktı `\\n` ile birleşir
    ve son satırda newline YOK (metrics-043 kalıbıyla aynı).
    """
    lines: list[str] = []
    lines += [
        "# HELP atlas_doctor_up Doctor command executed successfully",
        "# TYPE atlas_doctor_up gauge",
        "atlas_doctor_up 1",
        "# HELP atlas_doctor_warnings_total Number of doctor warnings (env + backend)",
        "# TYPE atlas_doctor_warnings_total gauge",
        f"atlas_doctor_warnings_total {len(report.get('warnings', []))}",
    ]

    quality = report.get("quality", {})
    if isinstance(quality, dict) and quality:
        lines += [
            "# HELP atlas_doctor_quality_healthy Per-field quality gate "
            "(1=no warning, 0=warning present)",
            "# TYPE atlas_doctor_quality_healthy gauge",
        ]
        for field in sorted(quality.keys()):
            value = quality[field]
            if not isinstance(value, dict):
                continue
            healthy = 0 if value.get("warning") else 1
            lines.append(
                f'atlas_doctor_quality_healthy{{field="{field}"}} {healthy}'
            )

    # SPEC 032.2 + 038: scan_src detay metrikleri (yalnız alan varsa)
    scan_src = quality.get("scan_src") if isinstance(quality, dict) else None
    if isinstance(scan_src, dict):
        hits = int(scan_src.get("total", 0) or 0)
        unique = int(scan_src.get("unique_hits", 0) or 0)
        lines += [
            "# HELP atlas_doctor_scan_src_hits_total Total secret-scan hits in src/",
            "# TYPE atlas_doctor_scan_src_hits_total gauge",
            f"atlas_doctor_scan_src_hits_total {hits}",
            "# HELP atlas_doctor_scan_src_unique_files Unique files with hits",
            "# TYPE atlas_doctor_scan_src_unique_files gauge",
            f"atlas_doctor_scan_src_unique_files {unique}",
        ]

    # SPEC 054: http_check detay metrikleri (yalnız alan varsa)
    http_check = quality.get("http_check") if isinstance(quality, dict) else None
    if isinstance(http_check, dict):
        # up=1 → 2xx başarı, 0 → herhangi bir sorun (warning != None)
        up = 0 if http_check.get("warning") else 1
        lines += [
            "# HELP atlas_doctor_http_check_up External HTTP endpoint "
            "reachable + 2xx (1=up, 0=down)",
            "# TYPE atlas_doctor_http_check_up gauge",
            f"atlas_doctor_http_check_up {up}",
        ]
        latency = http_check.get("latency_ms")
        if latency is not None:
            lines += [
                "# HELP atlas_doctor_http_check_latency_ms External HTTP endpoint latency in ms",
                "# TYPE atlas_doctor_http_check_latency_ms gauge",
                f"atlas_doctor_http_check_latency_ms {float(latency):.2f}",
            ]

    return "\n".join(lines)


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
    http_check_url: str | None = None,
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

    # SPEC 054: --http-check URL → HTTP GET sağlık kontrolü
    if http_check_url is not None:
        quality["http_check"] = _check_http(http_check_url)

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


def _doctor_schema_descriptor() -> dict[str, Any]:
    """SPEC 040: `atlas doctor --schema` için şema tanımı.

    JSON tüketicileri sürüm bump'ında (major = kırıcı) tanınabilir bir
    şema kontratına ihtiyaç duyar. Alan listesi + tip + kısa açıklama.

    NOT: Alan eklemek = uyumlu (schema_version aynı); kaldırma/rename =
    major bump. Bu tanımı `_collect_doctor_report` ile eş güncel tut.
    """
    return {
        "schema_version": _DOCTOR_SCHEMA_VERSION,
        "top_level": [
            {"name": "schema_version", "type": "str",
             "desc": "SPEC 032.4 major sürüm etiketi"},
            {"name": "backend", "type": "dict",
             "desc": "LLM backend seçimi ve konfigi (ATLAS_LLM)"},
            {"name": "retry_pricing", "type": "dict",
             "desc": "Retry/backoff/jitter + $ fiyat env'leri"},
            {"name": "storage", "type": "dict",
             "desc": "Vault/audit/sandbox/context/archive yolları"},
            {"name": "warnings", "type": "list[str]",
             "desc": "Toplu uyarı listesi (backend, ping, vs.)"},
            {"name": "quality", "type": "dict",
             "desc": "SPEC 032/032.1/032.2/038 kalite kapıları"},
            {"name": "ping", "type": "dict (opsiyonel)",
             "desc": "SPEC 021.2 — sadece --ping ile"},
        ],
        "quality_fields": [
            {"name": "decisions_drift", "spec": "032",
             "desc": "DECISIONS.md son giriş tarihi vs bugün"},
            {"name": "entry_count", "spec": "032.1",
             "desc": "Son N günde DECISIONS giriş sayısı"},
            {"name": "vault_health", "spec": "032.1",
             "desc": "vault/ not sayısı"},
            {"name": "scan_src", "spec": "032.2 + 038",
             "desc": "src/ sır taraması: total + unique_hits + sample_files"},
        ],
        "exit_codes": {
            "0": "sağlık kontrolü tamam",
            "8": "SPEC 029 — cache-hit oranı --alert altında",
            "9": "SPEC 032 — --strict altında herhangi bir quality warning",
        },
        "notes": [
            "SPEC 032.4: schema_version = major etiket; alan ekleme uyumlu.",
            "SPEC 032.5: --pretty ile indent=2 JSON.",
            "SPEC 038: scan_src.unique_hits = tekil dosya sayısı.",
            "SPEC 040: bu şema tanımı `atlas doctor --schema` ile yayımlanır.",
        ],
    }


def _cmd_doctor(args: argparse.Namespace) -> int:
    """SPEC 021 + 021.1 + 021.2 + 032 + 032.2 + 040: env sağlık + şema.

    `--json` bayrağı verilirse tek satır JSON; yoksa insan-okunur.
    `--ping` bayrağı Anthropic'e minimum request atar, latency+cost raporlar.
    `--strict` bayrağı DECISIONS drift uyarısı varsa exit 9 döner
    (SPEC 032). `--strict` yoksa mevcut davranış (exit 0) korunur.
    `--scan-src [PATH]` (SPEC 032.2) bayrağı verilirse `scan_secrets`
    kaynak dizinine uygulanır ve `quality.scan_src` alanı eklenir;
    bulgu varsa `--strict` altında exit 9 (tek kanal `_has_quality_warning`).
    `--schema` (SPEC 040) bayrağı sağlık kontrolü YAPMAZ — yalnız JSON
    şema tanımını basar (schema_version + alan listesi + exit kodları).
    """
    # SPEC 040: --schema kısa devre — hiçbir dizine dokunmaz, yalnız
    # şema tanımı JSON olarak basılır (idempotent, IO'suz).
    if getattr(args, "schema", False):
        import json as _json
        # --pretty ile birlikte indent=2 (tutarlılık)
        pretty = getattr(args, "pretty", False)
        indent = 2 if pretty else None
        print(_json.dumps(
            _doctor_schema_descriptor(), ensure_ascii=False, indent=indent,
        ))
        return 0

    # SPEC 080: --history-list kısa devre — sağlık kontrolü YAPMA,
    # yalnız .atlas/doctor-history/*.json listele (bilgi komutu).
    if getattr(args, "history_list", False):
        import json as _json_hl
        entries = _list_doctor_history()
        if getattr(args, "json", False):
            print(_json_hl.dumps(entries, ensure_ascii=False))
        else:
            print(
                f"=== ATLAS doctor --history-list "
                f"({_DEFAULT_DOCTOR_HISTORY_DIR}) — {len(entries)} snapshot ==="
            )
            if not entries:
                print("  (snapshot yok)")
            else:
                for e in entries:
                    print(
                        f"  {e['date']:<12}  {e['size_human']:>10}  "
                        f"{e['mtime']}"
                    )
        return 0

    # SPEC 032.2: --scan-src bayrağı → Path; yoksa None (bit-uyumlu).
    scan_src = getattr(args, "scan_src", None)
    scan_src_path = Path(scan_src) if scan_src else None
    # SPEC 054: --http-check URL (opsiyonel)
    http_check_url = getattr(args, "http_check", None)

    # SPEC 057: --diff önce kontrol edilir (--serve semantik reddi için).
    # --serve blocking; --diff verildiyse hemen semantik hata dön.
    diff_baseline_early = getattr(args, "diff", None)
    if diff_baseline_early and getattr(args, "serve", None):
        print("SPEC HATASI: --diff ve --serve birlikte kullanılamaz",
              file=sys.stderr)
        return 2

    # SPEC 051: --serve HOST:PORT → HTTP scrape endpoint (blocking).
    # Ping doctor için serve modunda anlamsız (her istek bir ping =
    # anthropic quota tüketimi); bu yüzden `--ping --serve` mutex.
    serve_spec = getattr(args, "serve", None)
    if serve_spec:
        from atlas_core.observability.prometheus_server import (
            parse_host_port,
            serve_prometheus_http,
        )
        if getattr(args, "ping", False):
            print(
                "SPEC HATASI: --ping ve --serve birlikte kullanılamaz "
                "(her istek anthropic ping = quota tüketimi)",
                file=sys.stderr,
            )
            return 2
        try:
            host, port = parse_host_port(serve_spec)
        except ValueError as exc:
            print(f"SPEC HATASI: {exc}", file=sys.stderr)
            return 2

        def _doctor_body() -> str:
            rep = _collect_doctor_report(
                scan_src_path=scan_src_path,
                http_check_url=http_check_url,
            )
            return _doctor_report_to_prometheus(rep)

        serve_prometheus_http(host, port, _doctor_body)
        return 0

    report = _collect_doctor_report(
        scan_src_path=scan_src_path,
        http_check_url=http_check_url,
    )

    if getattr(args, "ping", False):
        ping_info = _run_anthropic_ping(report["warnings"])
        if ping_info is not None:
            report["ping"] = ping_info

    # SPEC 062: --save-baseline [PATH] → mevcut raporu diske yaz + exit 0
    # (kalibrasyon amaçlı; diğer output mode'larıyla mutex).
    save_baseline = getattr(args, "save_baseline", None)
    auto_baseline = getattr(args, "auto_baseline", False)
    diff_baseline_arg = getattr(args, "diff", None)

    if save_baseline is not None:
        import json as _json_sb
        if diff_baseline_arg or auto_baseline:
            print(
                "SPEC HATASI: --save-baseline ile --diff/--auto-baseline "
                "birlikte kullanılamaz",
                file=sys.stderr,
            )
            return 2
        if getattr(args, "serve", None):
            print(
                "SPEC HATASI: --save-baseline ile --serve birlikte kullanılamaz",
                file=sys.stderr,
            )
            return 2
        if getattr(args, "format", None) == "prometheus":
            print(
                "SPEC HATASI: --save-baseline ile --format prometheus "
                "birlikte kullanılamaz",
                file=sys.stderr,
            )
            return 2
        target = Path(save_baseline)
        target.parent.mkdir(parents=True, exist_ok=True)
        report_json = _json_sb.dumps(report, ensure_ascii=False, indent=2)
        target.write_text(report_json, encoding="utf-8")
        print(f"[doctor] baseline yazıldı: {target}")
        # SPEC 080: default path kullanıldıysa tarihçe kopyası da yaz
        # (custom path → sadece PATH). Retention (`--history-keep N`)
        # opsiyonel.
        if target.resolve() == _DEFAULT_DOCTOR_BASELINE.resolve():
            from datetime import date as _date
            _DEFAULT_DOCTOR_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
            history_path = _DEFAULT_DOCTOR_HISTORY_DIR / (
                f"baseline-{_date.today().isoformat()}.json"
            )
            history_path.write_text(report_json, encoding="utf-8")
            print(f"[doctor] tarihce snapshot: {history_path}")
            # --history-keep N retention
            keep_hist = getattr(args, "history_keep", None)
            if keep_hist is not None:
                if keep_hist < 1:
                    print(
                        f"SPEC HATASI: --history-keep >= 1 olmalı: {keep_hist}",
                        file=sys.stderr,
                    )
                    return 2
                deleted = _prune_doctor_history(keep_hist)
                if deleted:
                    print(
                        f"[doctor] tarihce prune: {len(deleted)} eski silindi "
                        f"(keep={keep_hist})"
                    )
        return 0

    # SPEC 062: --auto-baseline → --diff için .atlas/doctor-baseline.json
    # otomatik kullan.
    if auto_baseline:
        if diff_baseline_arg:
            print(
                "SPEC HATASI: --auto-baseline ile --diff birlikte "
                "kullanılamaz (kaynak belirsiz)",
                file=sys.stderr,
            )
            return 2
        default_baseline = _DEFAULT_DOCTOR_BASELINE
        if not default_baseline.is_file():
            print(
                f"[--auto-baseline] baseline yok: {default_baseline}"
            )
            print(
                "İlk kalibrasyon için: atlas doctor --save-baseline"
            )
            return 0
        diff_baseline_arg = str(default_baseline)

    # SPEC 057: --diff BASELINE_JSON → mevcut raporla delta üret.
    diff_baseline = diff_baseline_arg
    if diff_baseline:
        import json as _json
        # Semantik mutex: --diff + --serve/--schema/--format anlamsız
        # (schema statik; serve blocking; format prometheus snapshot).
        if getattr(args, "serve", None):
            print("SPEC HATASI: --diff ve --serve birlikte kullanılamaz",
                  file=sys.stderr)
            return 2
        if getattr(args, "schema", False):
            print("SPEC HATASI: --diff ve --schema birlikte kullanılamaz",
                  file=sys.stderr)
            return 2
        if getattr(args, "format", None) == "prometheus":
            print(
                "SPEC HATASI: --diff ve --format prometheus birlikte kullanılamaz",
                file=sys.stderr,
            )
            return 2
        baseline_path = Path(diff_baseline)
        if not baseline_path.is_file():
            print(
                f"SPEC HATASI: baseline JSON yok: {baseline_path}",
                file=sys.stderr,
            )
            return 2
        try:
            baseline = _json.loads(baseline_path.read_text(encoding="utf-8"))
        except (OSError, _json.JSONDecodeError) as exc:
            print(
                f"SPEC HATASI: baseline JSON okunamadı: {exc}",
                file=sys.stderr,
            )
            return 2
        if not isinstance(baseline, dict):
            print(
                f"SPEC HATASI: baseline JSON kök obje olmalı: {type(baseline).__name__}",
                file=sys.stderr,
            )
            return 2

        delta = _diff_doctor_reports(baseline, report)

        if getattr(args, "json", False):
            pretty = getattr(args, "pretty", False)
            indent = 2 if pretty else None
            print(_json.dumps(delta, ensure_ascii=False, indent=indent))
        else:
            # ASCII-only markers (Windows cp1254 stdout capture uyumu:
            # pytest capsys `→ ⚠ ✓ ✗` gibi Unicode >0xFF karakterleri
            # cp1254 dup2'lu FD üzerinden encode edemez).
            print(
                f"=== ATLAS doctor --diff ({baseline_path.name} -> mevcut) ==="
            )
            if delta["schema_version_baseline"] != delta["schema_version_current"]:
                print(
                    f"  [!] schema_version degisti: "
                    f"{delta['schema_version_baseline']} -> "
                    f"{delta['schema_version_current']}"
                )
            if delta["warnings_added"]:
                print(f"\n  YENI uyarilar ({len(delta['warnings_added'])}):")
                for w in delta["warnings_added"]:
                    print(f"    + {w}")
            if delta["warnings_removed"]:
                print(f"\n  COZULEN uyarilar ({len(delta['warnings_removed'])}):")
                for w in delta["warnings_removed"]:
                    print(f"    - {w}")
            if delta["quality_deltas"]:
                print(f"\n  Quality alan degisiklikleri "
                      f"({len(delta['quality_deltas'])}):")
                for field, info in delta["quality_deltas"].items():
                    marker = {
                        "regressed":   "  [!]",
                        "resolved":    "  [+]",
                        "changed":     "  [~]",
                        "appeared":    "  [+]",
                        "disappeared": "  [-]",
                    }[info["change"]]
                    print(f"{marker} {field} [{info['change']}]")
                    if info["before_warning"]:
                        print(f"       once:  {info['before_warning']}")
                    if info["after_warning"]:
                        print(f"       sonra: {info['after_warning']}")
            if not (delta["warnings_added"] or delta["warnings_removed"]
                    or delta["quality_deltas"]):
                print("\n  OK degisiklik yok")

        if getattr(args, "strict", False) and delta["has_regression"]:
            print(
                "REGRESYON: --strict verildi, yeni bulgu var",
                file=sys.stderr,
            )
            return 9
        return 0

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

    # SPEC 047: --format prometheus (mutex --json + --schema, argparse'de).
    if getattr(args, "format", None) == "prometheus":
        print(_doctor_report_to_prometheus(report))
        # --strict format bağımsız: quality warning varsa exit 9 (raporu
        # Prometheus'a yayarız ama exit kod alertmanager tetikler).
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


def _build_metrics_prometheus_text(limit: int) -> str:
    """SPEC 051: `atlas metrics --format prometheus` text çıktısını
    string olarak üret (print YOK).

    Aynı format v0.0.4 satırları; canlı `.atlas/metrics.jsonl` her
    çağrıda tekrar okunur (HTTP scrape için).
    """
    import json as _json

    from atlas_core.orchestrator.planner import _metrics_path

    path = _metrics_path()
    records: list[dict[str, Any]] = []
    if path.is_file():
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                s = raw.strip()
                if not s:
                    continue
                try:
                    obj = _json.loads(s)
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
    denom = total_in + total_cc + total_cr
    hit_ratio = (total_cr / denom * 100) if denom else 0.0

    inflight_values = [
        int(r["inflight"])
        for r in tail
        if isinstance(r.get("inflight"), int) and r["inflight"] >= 0
    ]
    if inflight_values:
        inflight_avg = sum(inflight_values) / len(inflight_values)
        inflight_max = max(inflight_values)
        inflight_samples = len(inflight_values)
    else:
        inflight_avg = 0.0
        inflight_max = 0
        inflight_samples = 0

    price_in, price_out = _read_llm_prices()
    cost_total = 0.0
    if price_in > 0 or price_out > 0:
        cost_total = (
            total_in * price_in / 1_000_000
            + total_cc * price_in * 1.25 / 1_000_000
            + total_cr * price_in * 0.1 / 1_000_000
            + total_out * price_out / 1_000_000
        )

    lines: list[str] = [
        "# HELP atlas_metrics_records_total Number of LLM call records observed",
        "# TYPE atlas_metrics_records_total counter",
        f"atlas_metrics_records_total {len(tail)}",
        "# HELP atlas_metrics_tokens_prompt_total Prompt input token total",
        "# TYPE atlas_metrics_tokens_prompt_total counter",
        f"atlas_metrics_tokens_prompt_total {total_in}",
        "# HELP atlas_metrics_tokens_completion_total Completion output token total",
        "# TYPE atlas_metrics_tokens_completion_total counter",
        f"atlas_metrics_tokens_completion_total {total_out}",
        "# HELP atlas_metrics_cache_creation_tokens_total Cache creation token total",
        "# TYPE atlas_metrics_cache_creation_tokens_total counter",
        f"atlas_metrics_cache_creation_tokens_total {total_cc}",
        "# HELP atlas_metrics_cache_read_tokens_total Cache read token total",
        "# TYPE atlas_metrics_cache_read_tokens_total counter",
        f"atlas_metrics_cache_read_tokens_total {total_cr}",
        "# HELP atlas_metrics_cache_hit_ratio Cache-read share over total input tokens (0-1)",
        "# TYPE atlas_metrics_cache_hit_ratio gauge",
        f"atlas_metrics_cache_hit_ratio {hit_ratio / 100:.6f}",
        "# HELP atlas_metrics_cost_usd_total Estimated aggregate cost in USD",
        "# TYPE atlas_metrics_cost_usd_total counter",
        f"atlas_metrics_cost_usd_total {cost_total:.6f}",
    ]
    if inflight_samples > 0:
        lines += [
            "# HELP atlas_metrics_inflight_max Peak inflight LLM call count in window",
            "# TYPE atlas_metrics_inflight_max gauge",
            f"atlas_metrics_inflight_max {inflight_max}",
            "# HELP atlas_metrics_inflight_avg Average inflight LLM call count in window",
            "# TYPE atlas_metrics_inflight_avg gauge",
            f"atlas_metrics_inflight_avg {inflight_avg:.4f}",
        ]
    return "\n".join(lines)


def _filter_records_by_window(
    records: list[dict[str, Any]], window_minutes: float | None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """SPEC 076: `records` içinde `ts` alanı `now - window_minutes` sonrası
    olanları döner.

    - `window_minutes is None` → filtre YOK, orijinal liste (bit-uyumlu).
    - `ts` alanı yok / parse edilemez kayıt → filtre içi (nazik; SPEC 023
      metrik kayıtlarında `ts` her zaman vardır ama defensive).
    - `now` opsiyonel — test için `datetime.now()` override.

    Return: filtrelenmiş yeni liste (orijinal dokunulmaz).
    """
    from datetime import datetime, timedelta
    if window_minutes is None:
        return records
    ref = now if now is not None else datetime.now()
    threshold = ref - timedelta(minutes=window_minutes)
    out: list[dict[str, Any]] = []
    for r in records:
        ts_raw = r.get("ts")
        if not isinstance(ts_raw, str):
            out.append(r)  # ts yok → nazik dahil
            continue
        try:
            ts_dt = datetime.fromisoformat(ts_raw)
        except ValueError:
            out.append(r)  # parse edilemez → nazik dahil
            continue
        if ts_dt >= threshold:
            out.append(r)
    return out


def _group_records_by(
    records: list[dict[str, Any]], unit: str,
) -> list[dict[str, Any]]:
    """SPEC 081: metric records'ı `ts` alanına göre grupla.

    Args:
        records: `ts` (ISO 8601) alanı olan dict listesi.
        unit: `"hour"` (`YYYY-MM-DDTHH`) veya `"day"` (`YYYY-MM-DD`).

    Return: gruplar `[{key, records, tokens_in, tokens_out,
    cache_creation, cache_read}]`. Grup key'e göre sıralı (ISO 8601
    lex = kronolojik). `ts` yok/bozuk kayıt → `"unknown"` grup.
    """
    from datetime import datetime as _dt
    if unit not in ("hour", "day"):
        raise ValueError(f"unit hour|day olmalı: {unit}")
    grouped: dict[str, dict[str, Any]] = {}
    for r in records:
        ts_raw = r.get("ts")
        key = "unknown"
        if isinstance(ts_raw, str):
            try:
                ts_dt = _dt.fromisoformat(ts_raw)
                if unit == "hour":
                    key = ts_dt.strftime("%Y-%m-%dT%H")
                else:
                    key = ts_dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        g = grouped.setdefault(key, {
            "key": key,
            "records": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cache_creation": 0,
            "cache_read": 0,
        })
        g["records"] += 1
        g["tokens_in"] += int(r.get("in", 0) or 0)
        g["tokens_out"] += int(r.get("out", 0) or 0)
        g["cache_creation"] += int(r.get("cache_c", 0) or 0)
        g["cache_read"] += int(r.get("cache_r", 0) or 0)
    # unknown'ı sona koy, diğerleri lex sıralı
    keys = sorted(grouped.keys(), key=lambda k: (k == "unknown", k))
    return [grouped[k] for k in keys]


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
    # SPEC 076: --window MINUTES filtresi (limit ile ORTOGONAL — önce
    # window, sonra son N limit slice).
    window_min = getattr(args, "window", None)
    if window_min is not None:
        if window_min <= 0:
            print(
                f"SPEC HATASI: --window > 0 olmalı: {window_min}",
                file=sys.stderr,
            )
            return 2
        records = _filter_records_by_window(records, window_min)
    tail = records[-limit:]

    total_in = sum(int(r.get("in", 0) or 0) for r in tail)
    total_out = sum(int(r.get("out", 0) or 0) for r in tail)
    total_cc = sum(int(r.get("cache_c", 0) or 0) for r in tail)
    total_cr = sum(int(r.get("cache_r", 0) or 0) for r in tail)
    # cache-hit oranı: cache_r / (in + cache_c + cache_r)
    denom = total_in + total_cc + total_cr
    hit_ratio = (total_cr / denom * 100) if denom else 0.0

    # SPEC 023.2: inflight istatistiği (SPEC 039 alanının tüketimi).
    # `inflight` alanı olmayan satırlar skip (bit-uyumluluk: eski
    # kayıtlar veya inflight yayımı kapalı çağrılar). Tüm inflight
    # değerleri 0 ise ortalama 0, max 0 gösterilir.
    inflight_values = [
        int(r["inflight"])
        for r in tail
        if isinstance(r.get("inflight"), int) and r["inflight"] >= 0
    ]
    if inflight_values:
        inflight_avg = sum(inflight_values) / len(inflight_values)
        inflight_max = max(inflight_values)
        inflight_samples = len(inflight_values)
    else:
        inflight_avg = 0.0
        inflight_max = 0
        inflight_samples = 0

    # SPEC 051: --serve HOST:PORT → HTTP scrape endpoint (blocking)
    serve_spec = getattr(args, "serve", None)
    if serve_spec:
        from atlas_core.observability.prometheus_server import (
            parse_host_port,
            serve_prometheus_http,
        )
        try:
            host, port = parse_host_port(serve_spec)
        except ValueError as exc:
            print(f"SPEC HATASI: {exc}", file=sys.stderr)
            return 2
        serve_prometheus_http(
            host, port,
            lambda: _build_metrics_prometheus_text(limit),
        )
        return 0

    # SPEC 081: --group-by hour|day → aggregation, mevcut özet yerine
    # gruplar tablosu. --format/--serve/--alert ile mutex (semantik).
    group_by = getattr(args, "group_by", None)
    if group_by is not None:
        if getattr(args, "format", None) == "prometheus":
            print(
                "SPEC HATASI: --group-by ve --format prometheus birlikte "
                "kullanılamaz",
                file=sys.stderr,
            )
            return 2
        if getattr(args, "alert", None) is not None:
            print(
                "SPEC HATASI: --group-by ve --alert birlikte kullanılamaz "
                "(alert hit-ratio tekil değere, group aggregation)",
                file=sys.stderr,
            )
            return 2
        groups = _group_records_by(tail, group_by)
        if args.json:
            print(_json.dumps({
                "unit": group_by, "groups": groups,
            }, ensure_ascii=False))
        else:
            print(
                f"=== ATLAS metrics --group-by {group_by} — "
                f"{len(groups)} grup ==="
            )
            if not groups:
                print("  (kayit yok)")
                return 0
            key_w = max(20, *(len(g["key"]) for g in groups))
            print(
                f"  {'key':<{key_w}}  {'records':>7}  {'in':>8}  "
                f"{'out':>8}  {'cache_r':>8}"
            )
            for g in groups:
                print(
                    f"  {g['key']:<{key_w}}  {g['records']:>7}  "
                    f"{g['tokens_in']:>8}  {g['tokens_out']:>8}  "
                    f"{g['cache_read']:>8}"
                )
        return 0

    if args.json:
        print(_json.dumps(tail, ensure_ascii=False))
    elif getattr(args, "format", None) == "prometheus":
        # SPEC 043: Prometheus text v0.0.4 export
        # Cost tahmini için fiyat env'i lazım — reuse aşağıdaki mantığın
        # üstüne ekleme yapmadan burada hesapla.
        price_in, price_out = _read_llm_prices()
        cost_total = 0.0
        if price_in > 0 or price_out > 0:
            cost_total = (
                total_in * price_in / 1_000_000
                + total_cc * price_in * 1.25 / 1_000_000
                + total_cr * price_in * 0.1 / 1_000_000
                + total_out * price_out / 1_000_000
            )
        lines: list[str] = []
        lines += [
            "# HELP atlas_metrics_records_total Number of LLM call records observed",
            "# TYPE atlas_metrics_records_total counter",
            f"atlas_metrics_records_total {len(tail)}",
            "# HELP atlas_metrics_tokens_prompt_total Prompt input token total",
            "# TYPE atlas_metrics_tokens_prompt_total counter",
            f"atlas_metrics_tokens_prompt_total {total_in}",
            "# HELP atlas_metrics_tokens_completion_total Completion output token total",
            "# TYPE atlas_metrics_tokens_completion_total counter",
            f"atlas_metrics_tokens_completion_total {total_out}",
            "# HELP atlas_metrics_cache_creation_tokens_total Cache creation token total",
            "# TYPE atlas_metrics_cache_creation_tokens_total counter",
            f"atlas_metrics_cache_creation_tokens_total {total_cc}",
            "# HELP atlas_metrics_cache_read_tokens_total Cache read token total",
            "# TYPE atlas_metrics_cache_read_tokens_total counter",
            f"atlas_metrics_cache_read_tokens_total {total_cr}",
            "# HELP atlas_metrics_cache_hit_ratio Cache-read share over total input tokens (0-1)",
            "# TYPE atlas_metrics_cache_hit_ratio gauge",
            f"atlas_metrics_cache_hit_ratio {hit_ratio / 100:.6f}",
            "# HELP atlas_metrics_cost_usd_total Estimated aggregate cost in USD",
            "# TYPE atlas_metrics_cost_usd_total counter",
            f"atlas_metrics_cost_usd_total {cost_total:.6f}",
        ]
        # SPEC 023.2 tüketimi: inflight satırları yalnız veri varsa
        if inflight_samples > 0:
            lines += [
                "# HELP atlas_metrics_inflight_max Peak inflight LLM call count in window",
                "# TYPE atlas_metrics_inflight_max gauge",
                f"atlas_metrics_inflight_max {inflight_max}",
                "# HELP atlas_metrics_inflight_avg Average inflight LLM call count in window",
                "# TYPE atlas_metrics_inflight_avg gauge",
                f"atlas_metrics_inflight_avg {inflight_avg:.4f}",
            ]
        print("\n".join(lines))
    else:
        print(f"=== ATLAS metrics — son {limit} çağrı ===")
        print(f"  toplam: {len(tail)} çağrı")
        print(f"  input tokens:   {total_in}")
        print(f"  output tokens:  {total_out}")
        print(f"  cache creation: {total_cc}")
        print(f"  cache read:     {total_cr}")
        print(f"  cache-hit oranı: {hit_ratio:.1f}% ({total_cr} / {denom})")
        # SPEC 023.2: inflight istatistiği — yalnız veri varsa göster
        if inflight_samples > 0:
            print(
                f"  inflight avg/max: {inflight_avg:.2f} / {inflight_max} "
                f"({inflight_samples} kayıtta)"
            )
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
        msg = f"UYARI: cache-hit %{hit_ratio:.1f} < eşik %{alert:.1f}"
        print(msg, file=sys.stderr)
        # SPEC 059: --alert-email → SMTP notify (env ile config)
        if getattr(args, "alert_email", False):
            subject = (
                f"[ATLAS] metrics alert: cache-hit "
                f"{hit_ratio:.1f}% < {alert:.1f}%"
            )
            body = (
                f"{msg}\n\n"
                f"toplam: {len(tail)} çağrı\n"
                f"input tokens:   {total_in}\n"
                f"output tokens:  {total_out}\n"
                f"cache creation: {total_cc}\n"
                f"cache read:     {total_cr}\n"
                f"denominator:    {denom}\n"
            )
            ok, err = _send_alert_email(subject, body)
            if ok:
                print("[alert-email] gönderildi", file=sys.stderr)
            else:
                print(
                    f"[alert-email] gönderim başarısız: {err}",
                    file=sys.stderr,
                )
        # SPEC 064: --alert-webhook URL → POST JSON webhook (SMTP kardeşi)
        webhook_url = getattr(args, "alert_webhook", None)
        if webhook_url:
            payload = {
                "alert": "cache-hit",
                "hit_ratio_pct": round(hit_ratio, 2),
                "threshold_pct": alert,
                "records": len(tail),
                "tokens_in": total_in,
                "tokens_out": total_out,
                "cache_creation": total_cc,
                "cache_read": total_cr,
                "message": msg,
            }
            ok, err = _post_alert_webhook(webhook_url, payload)
            if ok:
                print("[alert-webhook] POST başarılı", file=sys.stderr)
            else:
                print(
                    f"[alert-webhook] POST başarısız: {err}",
                    file=sys.stderr,
                )
        # SPEC 068: --alert-slack URL → Slack incoming webhook özel format
        slack_url = getattr(args, "alert_slack", None)
        if slack_url:
            # Slack incoming webhook `{text}` bekler (attachments/blocks
            # opsiyonel; MVP `text`). ATLAS özel formatı: markdown-benzeri.
            text = (
                f":warning: *ATLAS cache-hit alert*\n"
                f"> {msg}\n"
                f"> records: `{len(tail)}` · "
                f"in: `{total_in}` · out: `{total_out}` · "
                f"cache_r: `{total_cr}`"
            )
            payload_slack = {"text": text}
            ok, err = _post_alert_webhook(slack_url, payload_slack)
            if ok:
                print("[alert-slack] POST başarılı", file=sys.stderr)
            else:
                print(
                    f"[alert-slack] POST başarısız: {err}",
                    file=sys.stderr,
                )
        return 8

    return 0


def _send_alert_email(subject: str, body: str) -> tuple[bool, str]:
    """SPEC 059: SMTP üzerinden alert emaili gönder (stdlib smtplib).

    Env sözleşmesi:
      - ATLAS_SMTP_HOST (zorunlu): SMTP server hostname
      - ATLAS_SMTP_PORT (default 587): SMTP server portu
      - ATLAS_SMTP_USER (opsiyonel): auth user
      - ATLAS_SMTP_PASSWORD (opsiyonel): auth password
      - ATLAS_SMTP_STARTTLS (default "1"): TLS upgrade ("1"|"true"|"True")
      - ATLAS_ALERT_FROM (zorunlu): gönderici adresi
      - ATLAS_ALERT_TO (zorunlu): virgülle liste (bir veya çok)

    Return: `(ok, error_message)`. Hata mesajı stderr'e basılır;
    exception yakalanır, ATLAS çıktı sözleşmesi bozulmaz.
    """
    import smtplib
    from email.message import EmailMessage

    host = os.environ.get("ATLAS_SMTP_HOST", "").strip()
    if not host:
        return False, "ATLAS_SMTP_HOST tanımlı değil"
    try:
        port = int(os.environ.get("ATLAS_SMTP_PORT", "587"))
    except ValueError:
        return False, "ATLAS_SMTP_PORT int olmalı"
    user = os.environ.get("ATLAS_SMTP_USER", "").strip() or None
    password = os.environ.get("ATLAS_SMTP_PASSWORD", "").strip() or None
    starttls = os.environ.get("ATLAS_SMTP_STARTTLS", "1").lower() in (
        "1", "true", "yes",
    )
    sender = os.environ.get("ATLAS_ALERT_FROM", "").strip()
    recipients_raw = os.environ.get("ATLAS_ALERT_TO", "").strip()
    if not sender:
        return False, "ATLAS_ALERT_FROM tanımlı değil"
    if not recipients_raw:
        return False, "ATLAS_ALERT_TO tanımlı değil"
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    if not recipients:
        return False, "ATLAS_ALERT_TO boş liste"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=10.0) as smtp:
            if starttls:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError, TimeoutError) as exc:
        return False, f"SMTP hatası: {exc}"
    return True, ""


def _post_alert_webhook(
    url: str, payload: dict[str, Any], timeout: float = 5.0,
) -> tuple[bool, str]:
    """SPEC 064: Alert JSON payload'ını POST webhook'a gönder.

    - stdlib `urllib.request` — dış bağımlılık YOK.
    - Content-Type: `application/json; charset=utf-8`.
    - 2xx → başarı; non-2xx / HTTPError / URLError / OSError → False + err.
    - Scheme http/https değil → False (SSRF savunma).

    Slack/Discord/Teams incoming webhook'ları kabul eder (aynı payload
    format). Kullanıcı istiyorsa provider-özel format için wrapper yazabilir.

    Return: `(ok, error_message)`. Exception yakalanır; ATLAS çıktı
    sözleşmesi bozulmaz.
    """
    import json as _json
    import urllib.error
    import urllib.request
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    if scheme not in ("http", "https"):
        return False, f"URL scheme geçersiz: '{scheme}' (http/https bekleniyor)"

    data = _json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "atlas-alert-webhook/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            status = resp.status
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, f"bağlantı hatası: {exc}"
    if not 200 <= status < 300:
        return False, f"HTTP {status}"
    return True, ""


def _cmd_vault_backup(args: argparse.Namespace) -> int:
    """SPEC 041: `atlas vault backup [--out PATH]` — vault/'ı .tar.gz sarmalar.

    Varsayılan konum: `<archive_root>/vault-YYYY-MM-DD-HHMM.tar.gz`.
    `--out PATH` verilirse doğrudan oraya yazar.

    SPEC 041.1:
      - `--auto`  → cron/scheduled explicit intent; `default_backup_path`
        kullanır (default davranışla aynı) ve audit action = `backup-auto`.
        `--out` ile birlikte kullanılırsa SPEC HATASI exit 2.
      - `--keep N` (N>=1) → backup yazıldıktan sonra `archive_root`
        içindeki `vault-*.tar.gz` yedekleri mtime desc sırayla ilk N
        tutulup geri kalanı silinir. `--out` verilmişse retention YOK
        sayılır (stderr uyarısı). Prune hatası → exit 6.
    """
    from atlas_core.memory.vault_backup import (
        VaultBackupError,
        backup_vault,
        default_backup_path,
        prune_backups,
    )
    vault_root = Path(args.vault_root) if args.vault_root else _vault_root()
    if not vault_root.is_dir():
        print(
            f"SPEC HATASI: vault dizini yok: {vault_root}",
            file=sys.stderr,
        )
        return 2

    auto = bool(getattr(args, "auto", False))
    out_arg = getattr(args, "out", None)
    if auto and out_arg:
        print(
            "SPEC HATASI: --auto ve --out birlikte kullanılamaz",
            file=sys.stderr,
        )
        return 2

    keep = getattr(args, "keep", None)
    if keep is not None and keep < 1:
        print(
            f"SPEC HATASI: --keep >= 1 olmalı: {keep}",
            file=sys.stderr,
        )
        return 2

    archive_root = Path(args.archive_root)
    if out_arg:
        out_path = Path(out_arg)
    else:
        archive_root.mkdir(parents=True, exist_ok=True)
        out_path = default_backup_path(archive_root)

    audit = AuditLog(_audit_path())
    try:
        result = backup_vault(vault_root, out_path)
    except VaultBackupError as exc:
        audit.record("atlas-vault", "backup-error", str(exc)[:180])
        print(f"YEDEK HATASI: {exc}", file=sys.stderr)
        return 6

    action = "backup-auto" if auto else "backup"
    audit.record("atlas-vault", action, str(result))
    print(f"vault yedeği yazıldı: {result}")

    # SPEC 041.1: retention
    if keep is not None:
        if out_arg:
            print(
                "UYARI: --out ile birlikte --keep YOK sayıldı "
                "(retention yalnızca archive_root'da çalışır)",
                file=sys.stderr,
            )
        else:
            try:
                deleted = prune_backups(archive_root, keep)
            except VaultBackupError as exc:
                audit.record("atlas-vault", "prune-error", str(exc)[:180])
                print(f"PRUNE HATASI: {exc}", file=sys.stderr)
                return 6
            for p in deleted:
                audit.record("atlas-vault", "prune", str(p))
            if deleted:
                print(
                    f"prune: {len(deleted)} eski yedek silindi "
                    f"(keep={keep})"
                )

    # SPEC 063: --encrypt PASSPHRASE → GPG symmetric AES256 → .tar.gz.gpg
    # SPEC 073: --recipient KEY_ID → GPG public-key asimetrik → .tar.gz.gpg
    # İkisi MUTEX (--encrypt ve --recipient birlikte kullanılamaz).
    encrypt_passphrase = getattr(args, "encrypt", None)
    recipient = getattr(args, "recipient", None)
    if encrypt_passphrase is not None and recipient:
        print(
            "SPEC HATASI: --encrypt ve --recipient birlikte kullanılamaz "
            "(iki farklı GPG modu: symmetric vs public-key)",
            file=sys.stderr,
        )
        return 2

    if encrypt_passphrase is not None:
        from atlas_core.memory.vault_backup import (
            VaultBackupError,
            encrypt_backup,
        )
        # Boş passphrase kabul edilmez (kullanıcı gafil düşmesin).
        if not encrypt_passphrase:
            print(
                "SPEC HATASI: --encrypt passphrase boş olamaz "
                "(env: ATLAS_BACKUP_PASSPHRASE veya bayraktan ver)",
                file=sys.stderr,
            )
            return 2
        enc_out = result.with_suffix(result.suffix + ".gpg")
        try:
            encrypt_backup(result, enc_out, encrypt_passphrase)
        except VaultBackupError as exc:
            audit.record("atlas-vault", "encrypt-error", str(exc)[:180])
            print(f"SIFRELEME HATASI: {exc}", file=sys.stderr)
            return 6
        # Plain dosyayı sil — encrypted çıktı yeni "yedek"
        try:
            result.unlink()
        except OSError:
            pass
        audit.record("atlas-vault", "encrypt", str(enc_out))
        print(f"vault yedeği şifrelendi: {enc_out}")
    elif recipient:
        # SPEC 073: public-key asimetrik encryption
        from atlas_core.memory.vault_backup import (
            VaultBackupError,
            encrypt_backup_recipient,
        )
        enc_out = result.with_suffix(result.suffix + ".gpg")
        try:
            encrypt_backup_recipient(result, enc_out, recipient)
        except VaultBackupError as exc:
            audit.record("atlas-vault", "encrypt-error", str(exc)[:180])
            print(f"SIFRELEME HATASI: {exc}", file=sys.stderr)
            return 6
        try:
            result.unlink()
        except OSError:
            pass
        audit.record(
            "atlas-vault", "encrypt-recipient",
            f"{recipient}: {enc_out}",
        )
        print(f"vault yedeği asimetrik şifrelendi (recipient={recipient}): {enc_out}")

    # SPEC 067: --keep-encrypted N → .tar.gz.gpg retention.
    # `--out` verilmişse retention YOK sayılır (SPEC 041.1 kalıbı — yalnız
    # archive_root'daki glob'a mantıklı).
    keep_enc = getattr(args, "keep_encrypted", None)
    if keep_enc is not None:
        if keep_enc < 1:
            print(
                f"SPEC HATASI: --keep-encrypted >= 1 olmalı: {keep_enc}",
                file=sys.stderr,
            )
            return 2
        if out_arg:
            print(
                "UYARI: --out ile birlikte --keep-encrypted YOK sayıldı "
                "(retention yalnızca archive_root'da çalışır)",
                file=sys.stderr,
            )
        else:
            from atlas_core.memory.vault_backup import prune_encrypted_backups
            try:
                deleted_enc = prune_encrypted_backups(archive_root, keep_enc)
            except VaultBackupError as exc:
                audit.record("atlas-vault", "prune-enc-error", str(exc)[:180])
                print(f"PRUNE HATASI: {exc}", file=sys.stderr)
                return 6
            for p in deleted_enc:
                audit.record("atlas-vault", "prune-encrypted", str(p))
            if deleted_enc:
                print(
                    f"prune-encrypted: {len(deleted_enc)} eski .gpg silindi "
                    f"(keep-encrypted={keep_enc})"
                )
    return 0


def _cmd_vault_restore(args: argparse.Namespace) -> int:
    """SPEC 041 + 066: `atlas vault restore <path> [--apply] [--decrypt]`.

    Dry-run varsayılan (yıkıcı: mevcut vault üstüne yazma).
    `--apply` gerekli.

    SPEC 066: `--decrypt [PASSPHRASE]` verilirse:
      - `<path>` `.tar.gz.gpg` beklenir; GPG decrypt → temp `.tar.gz` →
        restore_vault. Temp dosya restore sonrası silinir.
      - Passphrase bayraktan veya env `ATLAS_BACKUP_PASSPHRASE`.
      - Auto-detect: bayrak yoksa path `.gpg` ile bitiyorsa uyarı.

    Exit kodları:
      - 0: başarılı / dry-run
      - 2: SPEC HATASI (yedek yok, boş passphrase, vault_root arg)
      - 3: çakışma (hedef zaten var + boş değil)
      - 6: extract / GPG decrypt hatası
    """
    from atlas_core.memory.vault_backup import (
        VaultBackupError,
        decrypt_backup,
        decrypt_backup_recipient,
        restore_vault,
    )
    tar_path = Path(args.tar)
    if not tar_path.is_file():
        print(
            f"SPEC HATASI: yedek dosyası yok: {tar_path}",
            file=sys.stderr,
        )
        return 2
    target_root = Path(args.vault_root) if args.vault_root else _vault_root()

    decrypt_pass = getattr(args, "decrypt", None)
    decrypt_recipient = getattr(args, "decrypt_recipient", False)

    # SPEC 078: --decrypt + --decrypt-recipient MUTEX
    if decrypt_pass is not None and decrypt_recipient:
        print(
            "SPEC HATASI: --decrypt ve --decrypt-recipient birlikte "
            "kullanılamaz (symmetric vs asimetrik)",
            file=sys.stderr,
        )
        return 2

    # Auto-detect nazikliği: `.gpg` uzantısı + iki decrypt de yok → UYARI
    if (decrypt_pass is None and not decrypt_recipient
            and str(tar_path).endswith(".gpg")):
        print(
            "UYARI: dosya .gpg uzantılı ama --decrypt/--decrypt-recipient "
            "verilmedi — restore extract muhtemelen başarısız olacak.",
            file=sys.stderr,
        )

    if not args.apply:
        print("[dry-run] vault geri yükleme planı:")
        print(f"  yedek: {tar_path}")
        print(f"  hedef: {target_root}")
        if decrypt_pass is not None:
            print("  mod: GPG symmetric decrypt → restore (SPEC 066)")
        elif decrypt_recipient:
            print("  mod: GPG asimetrik decrypt (private key) → restore (SPEC 078)")
        if target_root.exists() and any(target_root.iterdir()):
            print("  UYARI: hedef mevcut ve boş değil — --apply exit 3")
        print(f"Uygulamak için: atlas vault restore {tar_path} --apply")
        return 0

    audit = AuditLog(_audit_path())

    # SPEC 066/078: --decrypt/--decrypt-recipient → önce decrypt, sonra restore
    plain_path = tar_path
    tmp_plain: Path | None = None
    if decrypt_pass is not None:
        if not decrypt_pass:
            print(
                "SPEC HATASI: --decrypt passphrase boş olamaz "
                "(env: ATLAS_BACKUP_PASSPHRASE veya bayraktan ver)",
                file=sys.stderr,
            )
            return 2
        # Temp plain dosya — restore sonrası silinir
        tmp_plain = target_root.parent / f".vault-restore-decrypt-{os.getpid()}.tar.gz"
        try:
            decrypt_backup(tar_path, tmp_plain, decrypt_pass)
        except VaultBackupError as exc:
            audit.record("atlas-vault", "decrypt-error", str(exc)[:180])
            print(f"DECRYPT HATASI: {exc}", file=sys.stderr)
            if tmp_plain.exists():
                try:
                    tmp_plain.unlink()
                except OSError:
                    pass
            return 6
        audit.record("atlas-vault", "decrypt", str(tmp_plain))
        plain_path = tmp_plain
    elif decrypt_recipient:
        # SPEC 078: asimetrik decrypt (private key + gpg-agent)
        tmp_plain = target_root.parent / f".vault-restore-decrypt-{os.getpid()}.tar.gz"
        try:
            decrypt_backup_recipient(tar_path, tmp_plain)
        except VaultBackupError as exc:
            audit.record("atlas-vault", "decrypt-recipient-error", str(exc)[:180])
            print(f"DECRYPT HATASI: {exc}", file=sys.stderr)
            if tmp_plain.exists():
                try:
                    tmp_plain.unlink()
                except OSError:
                    pass
            return 6
        audit.record("atlas-vault", "decrypt-recipient", str(tmp_plain))
        plain_path = tmp_plain

    try:
        result = restore_vault(plain_path, target_root)
    except VaultBackupError as exc:
        msg = str(exc)
        audit.record("atlas-vault", "restore-error", msg[:180])
        print(f"YEDEK HATASI: {msg}", file=sys.stderr)
        # Çakışma → 3; diğerleri → 6
        if "zaten var" in msg:
            return 3
        return 6
    finally:
        # SPEC 066: temp plain dosyayı sil (başarı VEYA hata sonrası)
        if tmp_plain is not None and tmp_plain.exists():
            try:
                tmp_plain.unlink()
            except OSError:
                pass

    audit.record("atlas-vault", "restore", str(result))
    print(f"vault geri yüklendi: {result}")
    return 0


def _cmd_vault_verify(args: argparse.Namespace) -> int:
    """SPEC 042: `atlas vault verify [--json] [--strict]` — graf sağlığı.

    Vault (Obsidian-uyumlu) üzerinde salt-okunur analiz:
      - kırık `[[wikilink]]` (hedef notu vault'ta yok)
      - orfan not (ne link veren ne link alan — bakım sinyali)
      - orfan tag (yalnız bir notta geçen `#tag`)

    Exit kodları:
      - 0: başarılı (bulgu olsa da; `--strict` yoksa uyarı)
      - 2: SPEC HATASI (vault dizini yok)
      - 4: `--strict` verildi ve rapor temiz değil
    """
    import json as _json

    from atlas_core.memory.vault import Vault
    from atlas_core.memory.vault_verify import format_report_markdown, verify_graph

    vault_root = Path(args.vault_root) if args.vault_root else _vault_root()
    if not vault_root.is_dir():
        print(
            f"SPEC HATASI: vault dizini yok: {vault_root}",
            file=sys.stderr,
        )
        return 2

    vault = Vault(vault_root)
    graph = vault.graph()
    report = verify_graph(graph)

    audit = AuditLog(_audit_path())
    audit.record("atlas-vault", "verify", str(vault_root))

    # SPEC 052: --dump-report PATH → markdown rapor otomatik dosyaya yaz.
    # Verify sonucu bit-uyumlu; sadece yan etki (dosya oluşturma).
    # Yazma hatası SESSİZ (hook contextinde commit'i patlatmamak için).
    dump_path = getattr(args, "dump_report", None)
    if dump_path:
        try:
            out = Path(dump_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                format_report_markdown(report, str(vault_root)),
                encoding="utf-8",
            )
        except OSError:
            pass  # rapor yazımı best-effort — verify çıktı sözleşmesi bozulmaz

    if getattr(args, "json", False):
        indent = 2 if getattr(args, "pretty", False) else None
        print(_json.dumps(report.to_dict(), ensure_ascii=False, indent=indent))
    else:
        print(f"=== ATLAS vault verify ({vault_root}) ===")
        print(f"  notlar:  {report.notes_total}")
        print(f"  linkler: {report.links_total}")
        print(f"  taglar:  {report.tags_total}")
        print(f"  kırık link: {len(report.broken_links)}")
        print(f"  orfan not:  {len(report.orphan_notes)}")
        print(f"  orfan tag:  {len(report.orphan_tags)}")
        if report.broken_links:
            print("\n  ilk 10 kırık link:")
            for b in report.broken_links[:10]:
                print(f"    {b.frm} -> {b.to}")
        if report.orphan_notes:
            print("\n  ilk 10 orfan not:")
            for n in report.orphan_notes[:10]:
                print(f"    {n}")
        if report.orphan_tags:
            print("\n  ilk 10 orfan tag:")
            for t in report.orphan_tags[:10]:
                print(f"    #{t}")
        if report.is_clean:
            print("\n  ✔ temiz")

    if getattr(args, "strict", False) and not report.is_clean:
        print(
            "SAĞLIK BAŞARISIZ: --strict verildi, bulgular var",
            file=sys.stderr,
        )
        return 4
    return 0


def _cmd_vault_fix_broken(args: argparse.Namespace) -> int:
    """SPEC 058: `atlas vault fix-broken [--apply]` — kırık wikilink'ler
    için stub not oluştur.

    Dry-run varsayılan (YIKICI). `--apply` ile gerçek yazma.

    Akış:
      1. Vault graf sağlığını çıkar (SPEC 042 `verify_graph`).
      2. `broken_links` içindeki her `to` hedefi için stub notu
         oluşturma planı (SPEC 058 `create_stub_notes`).
      3. Dry-run → plan raporu bas, exit 0.
      4. `--apply` → `<vault>/_stubs/` altına stub notları yaz; audit'e
         yaz.

    Exit kodları:
      - 0: başarılı (dry-run veya apply)
      - 2: SPEC HATASI (vault dizini yok)

    Bit-uyumluluk: `atlas vault verify` (SPEC 042) DEĞİŞMEDİ; ayrı
    alt-komut (SPEC 046 fix-orphans kalıbı).
    """
    from atlas_core.memory.vault import Vault
    from atlas_core.memory.vault_verify import (
        create_stub_notes,
        verify_graph,
    )

    vault_root = Path(args.vault_root) if args.vault_root else _vault_root()
    if not vault_root.is_dir():
        print(
            f"SPEC HATASI: vault dizini yok: {vault_root}",
            file=sys.stderr,
        )
        return 2

    vault = Vault(vault_root)
    report = verify_graph(vault.graph())
    if not report.broken_links:
        print("Kirik link yok — hicbir sey yapilmadi.")
        return 0

    if getattr(args, "target", None):
        target = Path(args.target)
    else:
        target = vault_root / "_stubs"

    apply = bool(getattr(args, "apply", False))
    actions = create_stub_notes(
        vault, report.broken_links, target, dry_run=not apply,
    )

    audit = AuditLog(_audit_path())
    if apply:
        created = len([a for a in actions if a.action == "created"])
        audit.record(
            "atlas-vault", "fix-broken",
            f"{created} stub -> {target}",
        )

    if apply:
        print(f"[fix-broken] {len(actions)} islem — hedef: {target}")
    else:
        print(f"[dry-run] {len(actions)} kirik hedef plani — hedef: {target}")

    for a in actions:
        try:
            rel_path = a.path.relative_to(vault_root)
        except ValueError:
            rel_path = a.path
        marker = {
            "planned": "  ..",
            "created": "  OK",
            "skipped": "  --",
        }[a.action]
        sources_str = ", ".join(a.sources) if a.sources else "?"
        print(f"{marker} {a.target}.md  <-  ({sources_str})  ->  {rel_path}")

    if not apply:
        print(f"\nUygulamak icin: atlas vault fix-broken --apply "
              f"--vault-root {vault_root}")
    return 0


def _cmd_vault_fix_orphans(args: argparse.Namespace) -> int:
    """SPEC 046: `atlas vault fix-orphans [--apply]` — orfan notları arşivle.

    Dry-run varsayılan (YIKICI işlem — mevcut `archive` kalıbı).
    `--apply` ile gerçek taşıma.

    Akış:
      1. Vault graf sağlığını çıkar (SPEC 042 `verify_graph`).
      2. `orphan_notes` listesindeki her not için hedef dosyayı bul
         (vault kökünde `rglob("<name>.md")`).
      3. Dry-run → plan raporu bas, exit 0.
      4. `--apply` → hedef klasörü oluştur, dosyaları `shutil.move` ile
         taşı; her taşımayı audit'e yaz.

    Exit kodları:
      - 0: başarılı (dry-run veya apply)
      - 2: SPEC HATASI (vault dizini yok)

    Bit-uyumluluk: `atlas vault verify` (SPEC 042) DEĞİŞMEDİ.
    """
    from atlas_core.memory.vault import Vault
    from atlas_core.memory.vault_verify import (
        archive_orphan_notes,
        verify_graph,
    )

    vault_root = Path(args.vault_root) if args.vault_root else _vault_root()
    if not vault_root.is_dir():
        print(
            f"SPEC HATASI: vault dizini yok: {vault_root}",
            file=sys.stderr,
        )
        return 2

    vault = Vault(vault_root)
    report = verify_graph(vault.graph())
    if not report.orphan_notes:
        print("Orfan not yok — hiçbir şey yapılmadı.")
        return 0

    today = date.today().isoformat()
    if getattr(args, "target", None):
        target = Path(args.target)
    else:
        target = vault_root / "_archive" / f"orphans-{today}"

    apply = bool(getattr(args, "apply", False))
    actions = archive_orphan_notes(
        vault, report.orphan_notes, target, dry_run=not apply,
    )

    audit = AuditLog(_audit_path())
    if apply:
        audit.record(
            "atlas-vault", "fix-orphans",
            f"{len([a for a in actions if a.action == 'moved'])} not -> {target}",
        )

    if apply:
        print(f"[fix-orphans] {len(actions)} işlem — hedef: {target}")
    else:
        print(f"[dry-run] {len(actions)} orfan not planı — hedef: {target}")
    for a in actions:
        rel_src = a.src.relative_to(vault_root)
        try:
            rel_dst = a.dst.relative_to(vault_root)
        except ValueError:
            rel_dst = a.dst  # target vault dışı ise mutlak yol
        marker = {"planned": "  ⋯", "moved": "  ✔", "skipped": "  ⚠"}[a.action]
        print(f"{marker} {rel_src}  →  {rel_dst}")
    if not apply:
        print(f"\nUygulamak için: atlas vault fix-orphans --apply "
              f"--vault-root {vault_root}")
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

_HOOK_SIGNATURE = "# atlas-hook v5"
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


def _run_npm_update(
    npm_bin: str, dry_run: bool, package: str | None = None,
) -> tuple[int, str, str]:
    """SPEC 037.1 + 050: `npm update` veya `npm outdated` çağır.

    Dry-run → `npm outdated --long [<package>]` (exit 0 veya 1;
    1 = güncellemesi olan paket var, hata değil). Uygula → `npm update
    [<package>]`.
    `cwd = tools/ai-cli` sabit.

    SPEC 050: `package` verilirse `npm outdated <package>` veya
    `npm update <package>` — sadece o paket etkilenir; kalan paketler
    dokunulmaz. `None` → mevcut davranış (hepsi güncellenir/kontrol edilir).

    Döner: `(returncode, stdout, stderr)`. Subprocess hatası → (-1, "", err).
    """
    if dry_run:
        args = [npm_bin, "outdated", "--long"]
    else:
        args = [npm_bin, "update"]
    if package:
        args.append(package)
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


def _run_npm_install(
    npm_bin: str, package: str,
) -> tuple[int, str, str]:
    """SPEC 060: `npm install <package> --save --save-exact=false` çağır.

    - `cwd = tools/ai-cli`.
    - `--save` dependencies güncellensin (npm 7+ default; explicit).
    - Sürüm belirtilmez → npm en son stable'ı çeker; `package.json`'a
      `^X.Y.Z` yazılır (npm defaults).

    Döner: `(returncode, stdout, stderr)`. Subprocess hatası → (-1, "", err).
    """
    args = [npm_bin, "install", package, "--save"]
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


def _run_npm_uninstall(
    npm_bin: str, package: str,
) -> tuple[int, str, str]:
    """SPEC 083: `npm uninstall <package>` çağır (`--save` ile deps'ten sil).

    - `cwd = tools/ai-cli`.
    - `--save` deps.json güncellensin (npm 7+ default; explicit).

    Döner: `(returncode, stdout, stderr)`. Subprocess hatası → (-1, "", err).
    """
    args = [npm_bin, "uninstall", package, "--save"]
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


def _resolve_ai_cli_bin(name: str) -> Path | None:
    """SPEC 037.3: `tools/ai-cli/node_modules/.bin/<name>` bin yolu.

    Windows önce `.cmd`; sonra çıplak isim; sonra `.exe`.
    Unix: çıplak isim (executable bit expected).
    Bulunamazsa `None`.
    """
    bin_dir = _AI_CLI_DIR / "node_modules" / ".bin"
    if not bin_dir.is_dir():
        return None
    if sys.platform == "win32":
        # Windows shim'leri npm .cmd olarak yaratır (shell exec eder)
        for suffix in (".cmd", ".exe", ""):
            candidate = bin_dir / f"{name}{suffix}"
            if candidate.is_file():
                return candidate
        return None
    # Unix
    candidate = bin_dir / name
    return candidate if candidate.is_file() else None


def _cmd_ai_cli_exec(args: argparse.Namespace) -> int:
    """SPEC 037.3: `atlas ai-cli exec <name> [args...]` — portable launcher.

    `tools/ai-cli/node_modules/.bin/<name>` (Windows: `.cmd`)
    shim'ini subprocess ile çalıştırır; kullanıcı argümanları forward.
    Exit kodu doğrudan yansıtılır.

    Hata durumları:
      - `tools/ai-cli/` yok → exit 2 + SPEC HATASI
      - bin bulunamadı → exit 2 + kullanıcıya paket adı öner
      - subprocess başlatma hatası → exit 2
    """
    if not _AI_CLI_DIR.is_dir():
        print(
            f"SPEC HATASI: {_AI_CLI_DIR} yok — portable ai-cli kurulumu bulunamadı",
            file=sys.stderr,
        )
        return 2
    name = args.name
    bin_path = _resolve_ai_cli_bin(name)
    if bin_path is None:
        print(
            f"SPEC HATASI: '{name}' bin bulunamadı "
            f"({_AI_CLI_DIR}/node_modules/.bin/). "
            f"Kurulu paketleri görmek için: atlas ai-cli list",
            file=sys.stderr,
        )
        return 2

    extra: list[str] = list(getattr(args, "cli_args", None) or [])
    cmd = [str(bin_path), *extra]
    try:
        # shell=False sabit; Windows .cmd shim'i doğrudan başlatılır
        # (cmd.exe /c değil — Python `subprocess` .cmd/.bat için özel yol).
        proc = subprocess.run(  # noqa: S603 - argv sabit + bin_path filtrelendi
            cmd,
            check=False,
        )
    except OSError as exc:
        print(f"SPEC HATASI: bin başlatılamadı: {exc}", file=sys.stderr)
        return 2
    return proc.returncode


def _dir_size_bytes(root: Path) -> int:
    """SPEC 037.4: Bir dizinin tüm dosyalarının toplam boyutu (byte).

    Sembolik link'ler izlenmez (dize sıklaştırma; döngü riski yok).
    Erişilemeyen dosya (silinmiş/OSError) skip edilir — best-effort.
    """
    total = 0
    if not root.is_dir():
        return 0
    for p in root.rglob("*"):
        try:
            if p.is_file() and not p.is_symlink():
                total += p.stat().st_size
        except OSError:
            continue
    return total


def _human_bytes(n: int) -> str:
    """SPEC 037.4: `1536 → '1.5 KB'`, `2_097_152 → '2.0 MB'`."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.2f} GB"


def _cmd_ai_cli_status(args: argparse.Namespace) -> int:
    """SPEC 037.4: `atlas ai-cli status <name> [--json]` — paket sağlık raporu.

    Exec çalıştırmadan paket durumunu raporlar:
      - `name`, `installed_version`, `declared_version` (package.json
        dependencies değeri), `up_to_date` (basit eşitlik/prefix eşleşmesi),
      - `install_dir` (`tools/ai-cli/node_modules/<name>`),
      - `size_bytes`, `size_human`, `bin_path` (varsa).

    Exit kodları:
      - 0: paket kurulu (bilgi komutu; up_to_date bilgisi rapor içinde)
      - 2: `tools/ai-cli/` yok VEYA paket dependencies'te değil VEYA
        kurulu değil → SPEC HATASI + `atlas ai-cli list` önerisi.
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

    name = args.name
    deps = data.get("dependencies", {}) if isinstance(data, dict) else {}
    if not isinstance(deps, dict) or name not in deps:
        print(
            f"SPEC HATASI: '{name}' package.json dependencies içinde yok. "
            f"Kurulu paketleri görmek için: atlas ai-cli list",
            file=sys.stderr,
        )
        return 2

    declared = str(deps[name])
    installed = _read_installed_version(name)
    if installed is None:
        print(
            f"SPEC HATASI: '{name}' kurulu değil "
            f"({_AI_CLI_DIR}/node_modules/{name}/ yok). "
            f"Kurmak için: atlas ai-cli update",
            file=sys.stderr,
        )
        return 2

    # up_to_date: declared sürüm sadeleştirmesi (^, ~, >=, boşluk sıyır)
    declared_clean = declared.lstrip("^~>=<! ").strip()
    up_to_date = installed == declared_clean

    install_dir = _AI_CLI_DIR / "node_modules" / name
    size_bytes = _dir_size_bytes(install_dir)
    bin_path = _resolve_ai_cli_bin(name)

    report = {
        "name": name,
        "installed_version": installed,
        "declared_version": declared,
        "up_to_date": up_to_date,
        "install_dir": str(install_dir),
        "size_bytes": size_bytes,
        "size_human": _human_bytes(size_bytes),
        "bin_path": str(bin_path) if bin_path else None,
    }

    if getattr(args, "json", False):
        print(_json.dumps(report, ensure_ascii=False))
        return 0

    print(f"=== ATLAS ai-cli status — {name} ===")
    print(f"  kurulu sürüm:   {installed}")
    print(f"  beklenen sürüm: {declared}")
    print(f"  güncel mi:      {'evet' if up_to_date else 'HAYIR'}")
    print(f"  kurulum yolu:   {install_dir}")
    print(f"  boyut:          {_human_bytes(size_bytes)} ({size_bytes} B)")
    if bin_path:
        print(f"  bin:            {bin_path}")
    else:
        print("  bin:            (yok — 'atlas ai-cli update' gerekebilir)")
    return 0


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


def _cmd_ai_cli_install(args: argparse.Namespace) -> int:
    """SPEC 060: `atlas ai-cli install <name>` — yeni paket ekle.

    `npm install <name> --save` wrap. Portable npm önce; sistem npm PATH
    fallback. `cwd = tools/ai-cli`.

    Exit kodları:
      - 0: yükleme başarılı; kullanıcıya doğrulama ipucu ver
        (`atlas ai-cli list`, `atlas ai-cli status <name>`).
      - 2: `tools/ai-cli/` yok / npm bulunamadı / subprocess çöktü.
      - npm exit yansıtıldığında ≠0 (yükleme başarısız).
    """
    if not _AI_CLI_DIR.is_dir():
        print(
            f"SPEC HATASI: {_AI_CLI_DIR} yok — portable ai-cli kurulumu bulunamadı",
            file=sys.stderr,
        )
        return 2

    package = args.name
    # Zaten kurulu mu? Bilgi ver, yine de npm çağır (idempotent üzerine yazar).
    _, err = _read_ai_cli_package_json()
    if err is not None:
        print(f"SPEC HATASI: {err}", file=sys.stderr)
        return 2

    npm_bin, source = _find_npm_bin()
    if npm_bin is None:
        print(
            "SPEC HATASI: npm bulunamadı — tools/node/ portable kurulumu "
            "yapın veya npm'i PATH'e ekleyin",
            file=sys.stderr,
        )
        return 2

    print(f"[ai-cli] npm install ({package}) ({source}: {npm_bin})")
    rc, out, stderr_ = _run_npm_install(npm_bin, package)
    if rc == -1:
        print(stderr_, file=sys.stderr)
        return 2
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if stderr_.strip():
        print(stderr_, end="" if stderr_.endswith("\n") else "\n",
              file=sys.stderr)

    if rc == 0:
        print(
            f"\n[ai-cli] '{package}' eklendi. Doğrulama:\n"
            f"  atlas ai-cli status {package}\n"
            f"  atlas ai-cli list"
        )
    return rc


def _cmd_ai_cli_uninstall(args: argparse.Namespace) -> int:
    """SPEC 083: `atlas ai-cli uninstall <name>` — paket kaldır.

    `npm uninstall <name> --save` wrap. `tools/ai-cli/package.json`
    dependencies'te olmalı; yoksa exit 2 SPEC HATASI + `atlas ai-cli
    list` önerisi.

    Exit kodları:
      - 0: yükleme kaldırıldı; kullanıcıya doğrulama (`ai-cli list`).
      - 2: `tools/ai-cli/` yok / paket deps'te yok / npm yok / subprocess.
      - npm exit ≠0 yansıtılır.
    """
    if not _AI_CLI_DIR.is_dir():
        print(
            f"SPEC HATASI: {_AI_CLI_DIR} yok — portable ai-cli kurulumu bulunamadı",
            file=sys.stderr,
        )
        return 2

    package = args.name
    data, err = _read_ai_cli_package_json()
    if err is not None:
        print(f"SPEC HATASI: {err}", file=sys.stderr)
        return 2
    assert data is not None
    deps = data.get("dependencies", {}) if isinstance(data, dict) else {}
    if not isinstance(deps, dict) or package not in deps:
        print(
            f"SPEC HATASI: '{package}' package.json dependencies içinde yok. "
            f"Kurulu paketleri görmek için: atlas ai-cli list",
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

    print(f"[ai-cli] npm uninstall ({package}) ({source}: {npm_bin})")
    rc, out, stderr_ = _run_npm_uninstall(npm_bin, package)
    if rc == -1:
        print(stderr_, file=sys.stderr)
        return 2
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if stderr_.strip():
        print(stderr_, end="" if stderr_.endswith("\n") else "\n",
              file=sys.stderr)

    if rc == 0:
        print(
            f"\n[ai-cli] '{package}' kaldırıldı. Doğrulama:\n"
            f"  atlas ai-cli list"
        )
    return rc


def _cmd_ai_cli_update(args: argparse.Namespace) -> int:
    """SPEC 037.1 + 050: `atlas ai-cli update [name] [--dry-run]` — npm wrap.

    - `tools/node/npm.cmd` (Windows portable) veya `tools/node/npm`
      (Unix portable) tercih; yoksa sistem `npm` (PATH).
    - `cwd = tools/ai-cli`.
    - `--dry-run` → `npm outdated --long [<name>]` (güncellemesi olan
      paketleri listele; exit 0 döner, npm 1 dönse bile "bulgu = hata
      değil").
    - Uygula → `npm update [<name>]`; npm exit kodunu doğrudan yansıt.
    - **SPEC 050**: `name` positional argümanı verilirse yalnız o paket
      etkilenir (sadece dependencies içindeki paketler kabul edilir;
      aksi hâlde exit 2 SPEC HATASI + `atlas ai-cli list` önerisi).
      `name` verilmezse mevcut davranış (hepsi).
    - npm bulunamadı → stderr uyarı + exit 2 (SPEC HATASI).
    - `tools/ai-cli/` yoksa → stderr uyarı + exit 2.
    """
    if not _AI_CLI_DIR.is_dir():
        print(
            f"SPEC HATASI: {_AI_CLI_DIR} yok — portable ai-cli kurulumu bulunamadı",
            file=sys.stderr,
        )
        return 2

    # SPEC 050: paket adı verildiyse dependencies'te olmalı
    package: str | None = getattr(args, "name", None) or None
    if package:
        data, err = _read_ai_cli_package_json()
        if err is not None:
            print(f"SPEC HATASI: {err}", file=sys.stderr)
            return 2
        assert data is not None
        deps = data.get("dependencies", {}) if isinstance(data, dict) else {}
        if not isinstance(deps, dict) or package not in deps:
            print(
                f"SPEC HATASI: '{package}' package.json dependencies içinde yok. "
                f"Kurulu paketleri görmek için: atlas ai-cli list",
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
    scope = f" ({package})" if package else ""
    print(f"[ai-cli] {label}{scope} ({source}: {npm_bin})")

    rc, out, err = _run_npm_update(npm_bin, dry_run, package=package)
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
    # SPEC 053: `atlas --version` — pyproject.toml ile eş güncel; kaynağı
    # `atlas_core.__version__` (paket metadata bağımsız, portable + wheel
    # kurulumu için de çalışır). `--version` action argparse'ın erken exit
    # yolu; alt-komut required=True olsa da parse_args sırasında `sys.exit(0)`
    # ile biter, dolayısıyla `atlas --version` alt-komut istemeden çalışır.
    from atlas_core import __version__ as _atlas_version
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"atlas {_atlas_version}",
        help="Sürüm bilgisini bas ve çık",
    )
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
    p_run.add_argument("--estimate", action="store_true",
                       help="SPEC 069: LLM çağırmadan planlanan çağrı+token+cost "
                            "tahmini bas (audit yok). Env "
                            "ATLAS_ESTIMATE_TOKENS_PER_CALL (default 500).")
    p_run.add_argument("--adaptive", action="store_true",
                       help="SPEC 072: --estimate ile birlikte, metrics.jsonl "
                            "son N call ortalamasını kullan (heuristik yerine). "
                            "< 3 kayıt → static fallback + UYARI.")
    p_run.add_argument("--adaptive-n", type=int, default=20,
                       help="SPEC 072: --adaptive için son N (default 20)")
    p_run.add_argument("--json", action="store_true",
                       help="SPEC 069: --estimate ile birlikte JSON çıktı")
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

    # SPEC 041: vault backup/restore
    p_vault = sub.add_parser(
        "vault",
        help="Vault yedekleme + geri yükleme (SPEC 041)",
    )
    vault_sub = p_vault.add_subparsers(dest="vault_cmd", required=True)
    p_vb = vault_sub.add_parser("backup", help="vault/'ı .tar.gz sarmalar")
    p_vb.add_argument("--out", default=None,
                      help="Yedek dosya yolu (yoksa <archive_root>/"
                           "vault-YYYY-MM-DD-HHMM.tar.gz)")
    p_vb.add_argument("--vault-root", default=None,
                      help="Vault kökü (env: ATLAS_VAULT; varsayılan vault)")
    p_vb.add_argument("--archive-root", default="archive",
                      help="Varsayılan yedek yazma kökü (--out yoksa)")
    p_vb.add_argument("--auto", action="store_true",
                      help="SPEC 041.1: cron/scheduled explicit intent — "
                           "default_backup_path kullanır ve audit'e "
                           "'backup-auto' yazar (--out ile çakışır)")
    p_vb.add_argument("--keep", type=int, default=None, metavar="N",
                      help="SPEC 041.1: backup sonrası archive_root'daki "
                           "vault-*.tar.gz yedekleri N tut, gerisini sil "
                           "(N>=1). --out ile birlikte YOK sayılır.")
    p_vb.add_argument("--encrypt", nargs="?",
                      const=os.environ.get("ATLAS_BACKUP_PASSPHRASE", ""),
                      default=None, metavar="PASSPHRASE",
                      help="SPEC 063: GPG symmetric (AES256) ile "
                           "<yedek>.tar.gz.gpg üret; plain silinir. "
                           "PASSPHRASE bayraktan veya env "
                           "ATLAS_BACKUP_PASSPHRASE. Env: ATLAS_GPG_BIN "
                           "gpg yolu override.")
    p_vb.add_argument("--recipient", default=None, metavar="KEY_ID",
                      help="SPEC 073: GPG public-key ile "
                           "<yedek>.tar.gz.gpg üret; plain silinir. "
                           "--encrypt ile MUTEX (symmetric vs public-key). "
                           "KEY_ID keyring'te olmalı (email/fingerprint). "
                           "--trust-model always (kullanıcı sözleşme kabulü).")
    p_vb.add_argument("--keep-encrypted", type=int, default=None, metavar="N",
                      help="SPEC 067: backup sonrası archive_root'daki "
                           "vault-*.tar.gz.gpg yedekleri N tut, gerisini "
                           "sil (N>=1). SPEC 041.1 --keep'in kardeşi; "
                           "ayrı glob (plain .tar.gz'e dokunmaz). "
                           "--out ile birlikte YOK sayılır.")
    p_vb.set_defaults(func=_cmd_vault_backup)
    p_vr = vault_sub.add_parser("restore", help=".tar.gz'i vault'a geri aç")
    p_vr.add_argument("tar", help="Yedek dosyası yolu (.tar.gz veya "
                                  ".tar.gz.gpg + --decrypt)")
    p_vr.add_argument("--apply", action="store_true",
                      help="Dry-run yerine gerçek extract çalıştır (yıkıcı)")
    p_vr.add_argument("--vault-root", default=None,
                      help="Hedef vault kökü (env: ATLAS_VAULT; varsayılan vault)")
    p_vr.add_argument("--decrypt", nargs="?",
                      const=os.environ.get("ATLAS_BACKUP_PASSPHRASE", ""),
                      default=None, metavar="PASSPHRASE",
                      help="SPEC 066: .tar.gz.gpg → GPG symmetric decrypt → "
                           "restore. PASSPHRASE bayraktan veya env "
                           "ATLAS_BACKUP_PASSPHRASE. Env: ATLAS_GPG_BIN.")
    p_vr.add_argument("--decrypt-recipient", action="store_true",
                      help="SPEC 078: .tar.gz.gpg → GPG asimetrik decrypt "
                           "(private key + gpg-agent) → restore. Passphrase "
                           "YOK; kullanıcı keyring/gpg-agent unlock yapmış "
                           "olmalı. --decrypt ile MUTEX.")
    p_vr.set_defaults(func=_cmd_vault_restore)
    # SPEC 042: vault verify (graf sağlığı)
    p_vv = vault_sub.add_parser(
        "verify", help="Vault graf sağlığı: kırık link/orfan not-tag (SPEC 042)",
    )
    p_vv.add_argument("--vault-root", default=None,
                      help="Vault kökü (env: ATLAS_VAULT; varsayılan vault)")
    p_vv.add_argument("--json", action="store_true",
                      help="JSON rapor çıktısı")
    p_vv.add_argument("--pretty", action="store_true",
                      help="--json ile birlikte girintili çıktı (indent=2)")
    p_vv.add_argument("--strict", action="store_true",
                      help="Bulgu varsa exit 4 (CI/pre-commit uyumlu)")
    p_vv.add_argument("--dump-report", default=None, metavar="PATH",
                      help="SPEC 052: rapor markdown olarak PATH'e yazılır "
                           "(dizin yoksa oluşturulur). Yazma hatası sessiz "
                           "geçilir — verify çıktı sözleşmesi bit-uyumlu.")
    p_vv.set_defaults(func=_cmd_vault_verify)
    # SPEC 046: vault fix-orphans (orfan notları arşivle — YIKICI)
    p_vfo = vault_sub.add_parser(
        "fix-orphans",
        help="Orfan notları vault/_archive/orphans-YYYY-MM-DD/ altına taşı "
             "(SPEC 046 — YIKICI, --apply gerekli)",
    )
    p_vfo.add_argument("--vault-root", default=None,
                       help="Vault kökü (env: ATLAS_VAULT; varsayılan vault)")
    p_vfo.add_argument("--apply", action="store_true",
                       help="Dry-run yerine gerçek taşıma (yıkıcı)")
    p_vfo.add_argument("--target", default=None, metavar="DIR",
                       help="Hedef dizin (varsayılan: "
                            "<vault>/_archive/orphans-YYYY-MM-DD)")
    p_vfo.set_defaults(func=_cmd_vault_fix_orphans)
    # SPEC 058: vault fix-broken (kırık wikilink'ler için stub not — YIKICI)
    p_vfb = vault_sub.add_parser(
        "fix-broken",
        help="Kırık [[wikilink]]'ler için stub not oluştur "
             "(SPEC 058 — YIKICI, --apply gerekli)",
    )
    p_vfb.add_argument("--vault-root", default=None,
                       help="Vault kökü (env: ATLAS_VAULT; varsayılan vault)")
    p_vfb.add_argument("--apply", action="store_true",
                       help="Dry-run yerine gerçek yazma (yıkıcı)")
    p_vfb.add_argument("--target", default=None, metavar="DIR",
                       help="Hedef dizin (varsayılan: <vault>/_stubs)")
    p_vfb.set_defaults(func=_cmd_vault_fix_broken)

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
    p_arc.add_argument("--restore", nargs="?", const="", default=None,
                       metavar="TASK_ID",
                       help="SPEC 033: <TASK_ID> arşivini pipeline/tasks/ "
                            "altına geri aç (dry-run varsayılan). "
                            "SPEC 071: bayraksız (`--restore --search P`) "
                            "arama sonucu tek arşiv otomatik seçilir.")
    p_arc.add_argument("--search", default=None, metavar="PATTERN",
                       help="SPEC 065: archive/*.tar.gz içinde dosya adı "
                            "regex ara (tar açılmaz — metadata yeter). "
                            "--json ile JSON çıktı.")
    p_arc.add_argument("--list", action="store_true",
                       help="SPEC 075: archive/*.tar.gz metadata listele "
                            "(task_id/date/size/member_count/mtime). "
                            "--json ile JSON çıktı.")
    p_arc.add_argument("--sort-by", default="name",
                       choices=["name", "size", "date", "members"],
                       help="SPEC 079: --list için sıralama anahtarı "
                            "(default 'name' — SPEC 075 bit-uyumlu).")
    p_arc.add_argument("--desc", action="store_true",
                       help="SPEC 079: --sort-by için azalan sıra")
    p_arc.add_argument("--json", action="store_true",
                       help="SPEC 065/075: --search veya --list ile birlikte "
                            "JSON çıktı")
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
    p_rep.add_argument("--serve", default=None, metavar="HOST:PORT",
                       help="SPEC 055: replay run listesini JSON HTTP endpoint "
                            "olarak yayımla (blocking; Ctrl+C ile durdur). "
                            "GET / veya /runs → --limit N kayıt "
                            "(application/json). --list/run-id ile mutex.")
    p_rep.set_defaults(func=_cmd_replay)

    p_met = sub.add_parser("metrics",
                           help="LLM çağrı metrikleri özeti (SPEC 023/029/076)")
    p_met.add_argument("--limit", type=int, default=20,
                       help="son N kaydı özetle (varsayılan 20)")
    p_met.add_argument("--window", type=float, default=None, metavar="MINUTES",
                       help="SPEC 076: sadece son N dakikadaki kayıtlar. "
                            "--limit ile ORTOGONAL (önce window sonra limit).")
    p_met.add_argument("--group-by", default=None, choices=["hour", "day"],
                       help="SPEC 081: records'ı ts alanına göre saat/gün "
                            "gruplarına ayır; aggregation tablosu. "
                            "--format/--alert ile MUTEX.")
    p_met_out = p_met.add_mutually_exclusive_group()
    p_met_out.add_argument("--json", action="store_true",
                           help="JSON liste çıktısı (ham kayıtlar)")
    p_met_out.add_argument("--format", default=None,
                           choices=["human", "prometheus"],
                           help="SPEC 043: 'prometheus' = Prometheus text "
                                "v0.0.4 export; 'human' = default insan çıktısı")
    p_met_out.add_argument("--serve", default=None, metavar="HOST:PORT",
                           help="SPEC 051: Prometheus text HTTP scrape "
                                "endpoint başlat (blocking; Ctrl+C ile durdur). "
                                "Ör: ':9090' veya '0.0.0.0:9090'")
    p_met.add_argument("--alert", type=float, default=None,
                       help="SPEC 029: cache-hit oranı bu %'den düşükse "
                            "stderr UYARI + exit 8 (0 kapatır)")
    p_met.add_argument("--alert-email", action="store_true",
                       help="SPEC 059: --alert eşiği aşıldığında SMTP "
                            "email at (env: ATLAS_SMTP_HOST/PORT/USER/"
                            "PASSWORD/STARTTLS + ATLAS_ALERT_FROM/TO). "
                            "Env eksik → uyarı stderr'e; exit 8 KORUR.")
    p_met.add_argument("--alert-webhook", default=None, metavar="URL",
                       help="SPEC 064: --alert eşiği aşıldığında URL'ye "
                            "POST JSON webhook at (Slack/Discord/Teams "
                            "incoming). --alert-email ile ortogonal. "
                            "Başarısız POST → stderr'e; exit 8 KORUR.")
    p_met.add_argument("--alert-slack", default=None, metavar="URL",
                       help="SPEC 068: --alert eşiği aşıldığında Slack "
                            "incoming webhook URL'sine `{text}` formatlı "
                            "POST at (markdown). --alert-webhook/-email ile "
                            "ORTOGONAL. Exit 8 KORUR.")
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
        help="tools/ai-cli/ paketlerini güncelle (portable npm wrap, SPEC 037.1 + 050)",
    )
    p_ai_up.add_argument(
        "name", nargs="?", default=None,
        help="SPEC 050: yalnız bu paketi güncelle (dependencies'te olmalı); "
             "verilmezse hepsi güncellenir",
    )
    p_ai_up.add_argument(
        "--dry-run", action="store_true",
        help="npm update yerine npm outdated çalıştır (yıkıcı işlem yok)",
    )
    p_ai_up.set_defaults(func=_cmd_ai_cli_update)
    p_ai_in = ai_sub.add_parser(
        "install",
        help="Yeni paketi tools/ai-cli/'ye ekle "
             "(npm install <name> --save wrap, SPEC 060)",
    )
    p_ai_in.add_argument("name", help="npm paket adı (ör. @scope/pkg)")
    p_ai_in.set_defaults(func=_cmd_ai_cli_install)
    p_ai_un = ai_sub.add_parser(
        "uninstall",
        help="Paketi tools/ai-cli/'den kaldır "
             "(npm uninstall <name> --save wrap, SPEC 083)",
    )
    p_ai_un.add_argument("name", help="package.json deps'te olan paket adı")
    p_ai_un.set_defaults(func=_cmd_ai_cli_uninstall)
    p_ai_ls = ai_sub.add_parser(
        "list",
        help="tools/ai-cli/ kurulu paketleri + beklenen sürüm (SPEC 037.2)",
    )
    p_ai_ls.add_argument("--json", action="store_true", help="JSON çıktı")
    p_ai_ls.set_defaults(func=_cmd_ai_cli_list)
    p_ai_ex = ai_sub.add_parser(
        "exec",
        help="Portable AI CLI'yı çalıştır: atlas ai-cli exec <name> [args...] (SPEC 037.3)",
    )
    p_ai_ex.add_argument("name", help="bin adı (ör. opencode, cline, kilo)")
    p_ai_ex.add_argument(
        "cli_args", nargs=argparse.REMAINDER, default=[],
        help="CLI'ya iletilecek argümanlar (opsiyonel; tümü aynen forward)",
    )
    p_ai_ex.set_defaults(func=_cmd_ai_cli_exec)
    p_ai_st = ai_sub.add_parser(
        "status",
        help="Paket sağlık raporu: sürüm+boyut+bin (SPEC 037.4)",
    )
    p_ai_st.add_argument("name", help="paket adı (ör. opencode-ai, cline)")
    p_ai_st.add_argument("--json", action="store_true", help="JSON çıktı")
    p_ai_st.set_defaults(func=_cmd_ai_cli_status)

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
    # SPEC 047: --json / --schema / --format üçlüsü mutex
    # (add_mutually_exclusive_group). store_true davranışı korunur.
    p_doc_out = p_doc.add_mutually_exclusive_group()
    p_doc_out.add_argument("--json", action="store_true",
                           help="JSON çıktı (CI/pre-flight uyumlu) — SPEC 021.1")
    p_doc_out.add_argument("--schema", action="store_true",
                           help="SPEC 040: sağlık kontrolü YAPMA, yalnız JSON "
                                "şema tanımını bas (alan listesi + exit kodları). "
                                "--pretty ile birlikte indent=2.")
    p_doc_out.add_argument("--format", default=None,
                           choices=["human", "prometheus"],
                           help="SPEC 047: 'prometheus' = Prometheus text v0.0.4 "
                                "export (up + warnings_total + quality_healthy "
                                "labels); 'human' = default insan çıktısı.")
    p_doc_out.add_argument("--serve", default=None, metavar="HOST:PORT",
                           help="SPEC 051: Prometheus scrape HTTP endpoint "
                                "başlat (blocking; Ctrl+C ile durdur). "
                                "Ör: ':9091' veya '0.0.0.0:9091'. --ping ile "
                                "mutex (her istek anthropic quota tüketir).")
    # SPEC 057: --diff mutex GRUBU DIŞINDA (ortogonal `--json` ile;
    # semantik mutex `--serve/--schema/--format` ile _cmd_doctor içinde).
    p_doc.add_argument("--diff", default=None, metavar="BASELINE_JSON",
                       help="SPEC 057: mevcut raporu BASELINE_JSON snapshot "
                            "ile karşılaştır; yeni/çözülen uyarılar + "
                            "quality alanı değişiklikleri raporlanır. "
                            "--json ile birlikte delta JSON. --strict + "
                            "regresyon → exit 9.")
    p_doc.add_argument("--http-check", default=None, metavar="URL",
                       help="SPEC 054: URL'ye HTTP GET at (timeout 5s); "
                            "quality.http_check alanına status + latency "
                            "raporla. 2xx dışı veya bağlantı hatası → "
                            "warning; --strict altında exit 9.")
    # SPEC 062: --auto-baseline + --save-baseline (--diff snapshot yönetimi)
    p_doc.add_argument("--auto-baseline", action="store_true",
                       help="SPEC 062: --diff için .atlas/doctor-baseline.json "
                            "otomatik kullan. Baseline yoksa nazik uyarı + "
                            "exit 0 (--save-baseline ile oluşturulur).")
    p_doc.add_argument("--save-baseline", nargs="?",
                       const=str(_DEFAULT_DOCTOR_BASELINE), default=None,
                       metavar="PATH",
                       help="SPEC 062: Mevcut raporu baseline olarak diske "
                            "yaz (default: .atlas/doctor-baseline.json). "
                            "--diff/--auto-baseline/--serve/--format prometheus "
                            "ile mutex. SPEC 080: default path kullanılırsa "
                            "tarihçe snapshot da yazılır "
                            "(.atlas/doctor-history/baseline-<today>.json).")
    p_doc.add_argument("--history-keep", type=int, default=None, metavar="N",
                       help="SPEC 080: --save-baseline default path ile birlikte, "
                            "tarihçe snapshot'larını N tut, gerisini sil.")
    p_doc.add_argument("--history-list", action="store_true",
                       help="SPEC 080: .atlas/doctor-history/*.json snapshot "
                            "listele (sağlık kontrolü yapma; --json ile JSON).")
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

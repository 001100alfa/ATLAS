"""SPEC 056 — .github/workflows/ YAML şablon bütünlük testleri.

Deployment artefaktı (kod DEĞİL). GitHub Actions runner'ında
çalıştırılamaz — burada sadece şema/kural doğrulaması:
- YAML valid parse
- Gerekli step'ler mevcut (checkout / setup-uv / uv sync / verify)
- ATLAS komut zinciri doğru (`atlas vault verify --strict --dump-report`)
- Fail durumunda PR comment step'i var
"""

from __future__ import annotations

from pathlib import Path

import pytest

# PyYAML olmayabilir; skip guard.
try:
    import yaml  # type: ignore[import-not-found]
except ImportError:
    yaml = None  # type: ignore[assignment]


_REPO = Path(__file__).resolve().parent.parent
_WORKFLOWS = _REPO / ".github" / "workflows"


pytestmark = pytest.mark.skipif(
    yaml is None,
    reason="PyYAML kurulu değil (opsiyonel test bağımlılığı)",
)


def _load(name: str) -> dict:
    """`workflows/<name>` YAML'ı dict olarak yükle."""
    path = _WORKFLOWS / name
    assert path.is_file(), f"eksik workflow: {path}"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)  # type: ignore[union-attr]


# ═════════════════════════════════════════════════════════════════════
# vault-health.yml
# ═════════════════════════════════════════════════════════════════════


def test_056_vault_health_yaml_valid() -> None:
    data = _load("vault-health.yml")
    assert isinstance(data, dict)
    assert data.get("name") == "vault-health"


def test_056_vault_health_tetikleyiciler() -> None:
    """push:main + pull_request; her ikisinde de vault/ path filtresi."""
    data = _load("vault-health.yml")
    # PyYAML `on:` anahtarını Python `True` (boolean) olarak parse
    # edebilir (YAML 1.1 backward-compat). Her iki key'i de dene.
    on = data.get("on") or data.get(True)
    assert on is not None, "'on' bloku yok"
    assert isinstance(on, dict), f"'on' bloku dict olmalı: {type(on)}"
    assert "push" in on
    assert on["push"]["branches"] == ["main"]
    assert "pull_request" in on
    # Her iki tetikleyicide de path filtresi olmalı
    for trigger in ("push", "pull_request"):
        paths = on[trigger].get("paths", [])
        assert any("vault" in p for p in paths), (
            f"{trigger}: vault path filtresi eksik: {paths}"
        )


def test_056_vault_health_permissions() -> None:
    """PR comment yazmak için `pull-requests: write` zorunlu."""
    data = _load("vault-health.yml")
    perms = data.get("permissions", {})
    assert perms.get("pull-requests") == "write"
    assert perms.get("contents") == "read"


def test_056_vault_health_concurrency() -> None:
    """Aynı ref'in eş zamanlı koşumlarını iptal et."""
    data = _load("vault-health.yml")
    conc = data.get("concurrency", {})
    assert "group" in conc
    assert conc.get("cancel-in-progress") is True


def test_056_vault_health_job_verify_var() -> None:
    """`verify` job'ı; ubuntu-latest; timeout var."""
    data = _load("vault-health.yml")
    jobs = data.get("jobs", {})
    assert "verify" in jobs
    verify = jobs["verify"]
    assert verify["runs-on"] == "ubuntu-latest"
    assert "timeout-minutes" in verify  # sonsuz koşum riski YOK


def test_056_vault_health_step_zinciri() -> None:
    """Gerekli step'ler: checkout + setup-uv + install + verify + comment + fail."""
    data = _load("vault-health.yml")
    steps = data["jobs"]["verify"]["steps"]
    uses = [s.get("uses") for s in steps if s.get("uses")]

    # actions/checkout
    assert any("actions/checkout" in u for u in uses), \
        f"actions/checkout eksik: {uses}"
    # setup-uv
    assert any("astral-sh/setup-uv" in u for u in uses), \
        f"astral-sh/setup-uv eksik: {uses}"
    # PR comment action
    assert any("peter-evans/create-or-update-comment" in u for u in uses), \
        f"peter-evans/create-or-update-comment eksik: {uses}"
    # artifact upload
    assert any("actions/upload-artifact" in u for u in uses), \
        f"actions/upload-artifact eksik: {uses}"

    # ATLAS komut zinciri (run: stepi)
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "atlas vault verify --strict --dump-report health.md" in run_blocks
    assert "uv sync" in run_blocks


def test_056_vault_health_comment_only_on_pr_failure() -> None:
    """PR comment step'i `github.event_name == 'pull_request'` gate'li."""
    data = _load("vault-health.yml")
    steps = data["jobs"]["verify"]["steps"]
    comment_step = next(
        (s for s in steps if s.get("uses", "").startswith("peter-evans/create-or-update-comment")),
        None,
    )
    assert comment_step is not None
    cond = comment_step.get("if", "")
    assert "pull_request" in cond
    assert "steps.verify.outputs.rc != '0'" in cond


def test_056_vault_health_fail_step_sonda() -> None:
    """Son step, verify rc != 0 ise `exit 1` ile job'ı fail eder."""
    data = _load("vault-health.yml")
    steps = data["jobs"]["verify"]["steps"]
    last = steps[-1]
    assert "steps.verify.outputs.rc != '0'" in last.get("if", "")
    assert "exit 1" in last.get("run", "")


def test_056_verify_step_continue_on_error() -> None:
    """Verify step'i `continue-on-error: true` — comment/artifact yazma
    şansı olmalı; ayrı bir fail step'i job'ı bitirir."""
    data = _load("vault-health.yml")
    steps = data["jobs"]["verify"]["steps"]
    verify_step = next(
        (s for s in steps if s.get("id") == "verify"), None,
    )
    assert verify_step is not None
    assert verify_step.get("continue-on-error") is True
    # rc'yi $GITHUB_OUTPUT'a yazsın
    assert "$GITHUB_OUTPUT" in verify_step.get("run", "")


# ═════════════════════════════════════════════════════════════════════
# SPEC 070: atlas-doctor.yml
# ═════════════════════════════════════════════════════════════════════


def test_070_atlas_doctor_yaml_valid() -> None:
    data = _load("atlas-doctor.yml")
    assert isinstance(data, dict)
    assert data.get("name") == "atlas-doctor"


def test_070_atlas_doctor_tetikleyiciler() -> None:
    data = _load("atlas-doctor.yml")
    on = data.get("on") or data.get(True)
    assert isinstance(on, dict)
    assert on["push"]["branches"] == ["main"]
    assert "pull_request" in on
    for trig in ("push", "pull_request"):
        paths = on[trig].get("paths", [])
        assert any("src/" in p for p in paths), f"{trig}: src/ eksik"


def test_070_atlas_doctor_permissions_concurrency() -> None:
    data = _load("atlas-doctor.yml")
    assert data["permissions"]["pull-requests"] == "write"
    assert data["permissions"]["contents"] == "read"
    assert data["concurrency"]["cancel-in-progress"] is True


def test_070_atlas_doctor_job_zinciri() -> None:
    """Job doctor: checkout + uv + install + atlas doctor + artifact +
    fail step."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    uses = [s.get("uses") for s in steps if s.get("uses")]
    assert any("actions/checkout" in u for u in uses)
    assert any("astral-sh/setup-uv" in u for u in uses)
    assert any("actions/upload-artifact" in u for u in uses)
    assert any("peter-evans/create-or-update-comment" in u for u in uses)
    # ATLAS komut zinciri
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "atlas doctor --strict --scan-src" in run_blocks
    # SPEC 062: --auto-baseline dallanma
    assert "atlas doctor --strict --auto-baseline" in run_blocks
    assert ".atlas/doctor-baseline.json" in run_blocks


def test_070_doctor_step_continue_on_error() -> None:
    """`doctor` step continue-on-error: true — sonraki step'ler koşsun."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    doctor_step = next(s for s in steps if s.get("id") == "doctor")
    assert doctor_step.get("continue-on-error") is True
    assert "$GITHUB_OUTPUT" in doctor_step.get("run", "")


def test_070_doctor_fail_step_iki_kaynak() -> None:
    """Fail step: rc_strict OR rc_diff ≠ '0' → exit 1."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    last = steps[-1]
    cond = last.get("if", "")
    assert "rc_strict != '0'" in cond
    assert "rc_diff != '0'" in cond
    assert "exit 1" in last.get("run", "")


# ═════════════════════════════════════════════════════════════════════
# SPEC 077: no-docker.yml
# ═════════════════════════════════════════════════════════════════════


def test_077_no_docker_yaml_valid() -> None:
    data = _load("no-docker.yml")
    assert isinstance(data, dict)
    assert data.get("name") == "no-docker"


def test_077_no_docker_tetikleyiciler() -> None:
    """push[main] + pull_request tümü (path filtresi yok — her PR gate)."""
    data = _load("no-docker.yml")
    on = data.get("on") or data.get(True)
    assert isinstance(on, dict)
    assert on["push"]["branches"] == ["main"]
    assert "pull_request" in on


def test_077_no_docker_job_run_zinciri() -> None:
    data = _load("no-docker.yml")
    steps = data["jobs"]["scan"]["steps"]
    uses = [s.get("uses") for s in steps if s.get("uses")]
    assert any("actions/checkout" in u for u in uses)
    # git ls-files pattern arama
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "git ls-files" in run_blocks
    assert "Dockerfile" in run_blocks
    assert "docker-compose" in run_blocks
    assert ".dockerignore" in run_blocks
    assert "exit 1" in run_blocks


def test_077_no_docker_hizli_timeout() -> None:
    """Docker taraması hızlı olmalı — timeout ≤ 5dk."""
    data = _load("no-docker.yml")
    assert data["jobs"]["scan"]["timeout-minutes"] <= 5


def test_077_no_docker_artefakt_repoda_yok() -> None:
    """Şu an repo'da (git tracked) Docker artefaktı olmadığı sözleşme.

    `git ls-files` git-ignored dizinleri (`runtime/`, `tools/ai-cli/
    node_modules/`, ...) OTOMATİK atlar — CI ile eşdeğer semantik.
    """
    import subprocess as _sp
    result = _sp.run(  # noqa: S603 - argv sabit
        ["git", "ls-files",
         "Dockerfile", "Dockerfile.*",
         "docker-compose.yml", "docker-compose.yaml",
         ".dockerignore",
         "**/Dockerfile", "**/Dockerfile.*",
         "**/docker-compose.yml", "**/docker-compose.yaml",
         "**/.dockerignore"],
        cwd=str(_REPO),
        capture_output=True, text=True, timeout=30, check=False,
    )
    tracked = [ln for ln in result.stdout.splitlines() if ln.strip()]
    assert tracked == [], (
        f"Docker artefakti tracked (SPEC 077 ihlali): {tracked}"
    )


# ═════════════════════════════════════════════════════════════════════
# SPEC 074: atlas-metrics.yml
# ═════════════════════════════════════════════════════════════════════


def test_074_atlas_metrics_yaml_valid() -> None:
    data = _load("atlas-metrics.yml")
    assert isinstance(data, dict)
    assert data.get("name") == "atlas-metrics"


def test_074_atlas_metrics_tetikleyiciler() -> None:
    """push[main]+PR; `.atlas/metrics.jsonl` path filtresi."""
    data = _load("atlas-metrics.yml")
    on = data.get("on") or data.get(True)
    assert isinstance(on, dict)
    assert on["push"]["branches"] == ["main"]
    for trig in ("push", "pull_request"):
        paths = on[trig].get("paths", [])
        assert any("metrics.jsonl" in p for p in paths), (
            f"{trig}: metrics.jsonl path eksik: {paths}"
        )


def test_074_atlas_metrics_permissions_concurrency() -> None:
    data = _load("atlas-metrics.yml")
    assert data["permissions"]["pull-requests"] == "write"
    assert data["concurrency"]["cancel-in-progress"] is True


def test_074_atlas_metrics_uc_format_uretir() -> None:
    """human + json + prometheus üç artifact üretir."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "atlas metrics --limit" in run_blocks
    assert "--json" in run_blocks
    assert "--format prometheus" in run_blocks
    # 3 artifact dosya adı
    assert "metrics-human.txt" in run_blocks
    assert "metrics.json" in run_blocks
    assert "metrics.prom" in run_blocks


def test_074_atlas_metrics_pr_comment_kosullu() -> None:
    """PR comment step: sadece PR + has_data=true."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    comment_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("peter-evans/create-or-update-comment")),
        None,
    )
    assert comment_step is not None
    cond = comment_step.get("if", "")
    assert "pull_request" in cond
    assert "has_data" in cond


def test_074_atlas_metrics_artifact_upload_always() -> None:
    """artifact upload `if: always()` — job fail'de bile artifact atılsın."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    assert upload_step.get("if") == "always()"


# ═════════════════════════════════════════════════════════════════════
# SPEC 089 — atlas-ci-status.yml (scheduled daily drift scan)
# ═════════════════════════════════════════════════════════════════════


def test_089_atlas_ci_status_yaml_valid() -> None:
    data = _load("atlas-ci-status.yml")
    assert isinstance(data, dict)
    assert data.get("name") == "atlas-ci-status"


def test_089_atlas_ci_status_schedule_daily() -> None:
    """cron: her gün 06:00 UTC (deterministik)."""
    data = _load("atlas-ci-status.yml")
    on = data.get("on") or data.get(True)
    assert isinstance(on, dict)
    assert "schedule" in on
    crons = on["schedule"]
    assert isinstance(crons, list) and len(crons) >= 1
    assert any(c.get("cron") == "0 6 * * *" for c in crons)


# ═════════════════════════════════════════════════════════════════════
# SPEC 141 — atlas-ci-status.yml alert-webhook gate
# ═════════════════════════════════════════════════════════════════════


def test_141_atlas_ci_status_alert_webhook_step() -> None:
    """`Post ci-status alert webhook (SPEC 131/141)` step var."""
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    step = next(
        (s for s in steps
         if "ci-status alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "curl" in run
    assert "ALERT_WEBHOOK_URL" in run
    assert '"alert":"ci-status"' in run


def test_141_atlas_ci_status_alert_webhook_env() -> None:
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    step = next(
        (s for s in steps
         if "ci-status alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    env = step.get("env", {})
    assert "ATLAS_ALERT_WEBHOOK_URL" in str(env.get("ALERT_WEBHOOK_URL", ""))


def test_141_atlas_ci_status_alert_webhook_conditional() -> None:
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    step = next(
        (s for s in steps
         if "ci-status alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    cond = step.get("if", "")
    assert "ALERT_WEBHOOK_URL" in cond
    assert "rc" in cond


def test_141_atlas_ci_status_alert_webhook_continue_on_error() -> None:
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    step = next(
        (s for s in steps
         if "ci-status alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert step.get("continue-on-error") is True


def test_119_atlas_ci_status_weekly_cron() -> None:
    """SPEC 119: haftalık cron `0 7 * * 1` eklenir; daily bozulmaz."""
    data = _load("atlas-ci-status.yml")
    on = data.get("on") or data.get(True)
    crons = on["schedule"]
    values = {c.get("cron") for c in crons}
    assert "0 6 * * *" in values  # SPEC 089 daily
    assert "0 7 * * 1" in values  # SPEC 119 weekly


def test_089_atlas_ci_status_workflow_dispatch() -> None:
    """Manuel tetik `workflow_dispatch` var."""
    data = _load("atlas-ci-status.yml")
    on = data.get("on") or data.get(True)
    assert "workflow_dispatch" in on


def test_089_atlas_ci_status_permissions() -> None:
    """issues:write (issue aç), contents:read (checkout)."""
    data = _load("atlas-ci-status.yml")
    perms = data.get("permissions", {})
    assert perms.get("issues") == "write"
    assert perms.get("contents") == "read"


def test_089_atlas_ci_status_runs_gen_ci_badges() -> None:
    """Job `python tools/scripts/gen_ci_badges.py --check` çağırır."""
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "gen_ci_badges.py --check" in run_blocks


def test_089_atlas_ci_status_creates_issue_on_drift() -> None:
    """Drift → issue açma step'i (peter-evans/create-issue-from-file@v5)."""
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    issue_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("peter-evans/create-issue-from-file")),
        None,
    )
    assert issue_step is not None
    cond = issue_step.get("if", "")
    assert "rc" in cond and "!=" in cond


# ═════════════════════════════════════════════════════════════════════
# SPEC 125 — atlas-ci-status.yml drift diff artifact
# ═════════════════════════════════════════════════════════════════════


def test_125_atlas_ci_status_drift_artifact_step() -> None:
    """`Upload drift diff artifact (SPEC 125)` step var."""
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    step = next(
        (s for s in steps
         if "upload drift" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert step.get("uses", "").startswith("actions/upload-artifact")


def test_125_atlas_ci_status_drift_artifact_conditional() -> None:
    """Artifact step yalnız drift varsa (rc != 0) çalışır."""
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    step = next(
        (s for s in steps
         if "upload drift" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    cond = step.get("if", "")
    assert "rc" in cond and "!=" in cond


def test_125_atlas_ci_status_drift_artifact_path() -> None:
    """Artifact path README.md + drift-issue.md içerir."""
    data = _load("atlas-ci-status.yml")
    steps = data["jobs"]["drift-scan"]["steps"]
    step = next(
        (s for s in steps
         if "upload drift" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    path_str = str(step.get("with", {}).get("path", ""))
    assert "README.md" in path_str
    assert "drift-issue.md" in path_str


def test_089_atlas_ci_status_readme_badge_row() -> None:
    """README ci-status bloğunda `atlas-ci-status` satırı var."""
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    assert "atlas-ci-status.yml" in readme
    assert "| atlas-ci-status |" in readme


# ═════════════════════════════════════════════════════════════════════
# SPEC 095 — atlas-metrics.yml --with-cost entegrasyonu
# ═════════════════════════════════════════════════════════════════════


def test_095_atlas_metrics_cost_step_exists() -> None:
    """`Generate cost by day` step'i var + --with-cost + --group-by day."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    cost_step = next(
        (s for s in steps if "cost by day" in s.get("name", "").lower()),
        None,
    )
    assert cost_step is not None
    run = cost_step.get("run", "")
    assert "--group-by day" in run
    assert "--with-cost" in run
    assert "metrics-cost-by-day.json" in run


def test_095_atlas_metrics_cost_conditional_has_data() -> None:
    """Cost step yalnız has_data=true iken çalışır (env fiyat yok
    fail-safe)."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    cost_step = next(
        (s for s in steps if "cost by day" in s.get("name", "").lower()),
        None,
    )
    assert cost_step is not None
    cond = cost_step.get("if", "")
    assert "has_data" in cond
    assert "true" in cond


def test_095_atlas_metrics_cost_artifact_uploaded() -> None:
    """Upload artifact listesinde `metrics-cost-by-day.json` var."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert "metrics-cost-by-day.json" in path_str


def test_095_atlas_metrics_mevcut_3_artifact_dokunulmadi() -> None:
    """SPEC 074 mevcut 3 artifact (`metrics-human.txt`, `metrics.json`,
    `metrics.prom`) upload listesinde AYNI (BİT-UYUMLU)."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert "metrics-human.txt" in path_str
    assert "metrics.json" in path_str
    assert "metrics.prom" in path_str


# ═════════════════════════════════════════════════════════════════════
# SPEC 100 — atlas-doctor.yml --diff-history-all entegrasyonu
# ═════════════════════════════════════════════════════════════════════


def test_100_atlas_doctor_diff_history_all_step() -> None:
    """`Generate diff-history-all trend` step'i var + `--diff-history-all --json`."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "diff-history-all trend" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "--diff-history-all" in run
    assert "--json" in run
    assert "doctor-diff-history-all.json" in run


def test_100_atlas_doctor_diff_history_all_fallback() -> None:
    """`||` fallback bos snapshots (workflow durmaz)."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "diff-history-all trend" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert '||' in run
    assert '"snapshots":[]' in run


def test_100_atlas_doctor_artifact_uploaded() -> None:
    """Upload artifact listesinde `doctor-diff-history-all.json`."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert "doctor-diff-history-all.json" in path_str


# ═════════════════════════════════════════════════════════════════════
# SPEC 130 — atlas-doctor.yml --diff-history-all --strict gate
# ═════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════════════
# SPEC 135 — atlas-doctor.yml alert-webhook gate
# ═════════════════════════════════════════════════════════════════════


def test_135_atlas_doctor_alert_webhook_step() -> None:
    """`Post doctor alert webhook (SPEC 131/135)` step var."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "post doctor alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "curl" in run
    assert "ALERT_WEBHOOK_URL" in run


def test_135_atlas_doctor_alert_webhook_env() -> None:
    """Env `ALERT_WEBHOOK_URL: secrets.ATLAS_ALERT_WEBHOOK_URL`."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "post doctor alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    env = step.get("env", {})
    assert "ATLAS_ALERT_WEBHOOK_URL" in str(env.get("ALERT_WEBHOOK_URL", ""))


def test_135_atlas_doctor_alert_webhook_conditional() -> None:
    """Conditional: env + rc != 0."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "post doctor alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    cond = step.get("if", "")
    assert "ALERT_WEBHOOK_URL" in cond
    assert "rc_strict" in cond


def test_135_atlas_doctor_alert_webhook_continue_on_error() -> None:
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "post doctor alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert step.get("continue-on-error") is True


def test_130_atlas_doctor_history_gate_step() -> None:
    """`Doctor history regression gate (SPEC 097/130)` step var."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "history regression gate" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "--diff-history-all" in run
    assert "--strict" in run


def test_130_atlas_doctor_history_gate_id() -> None:
    """Step id `history_gate` — fail step conditional için."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    step = next(
        (s for s in steps
         if "history regression gate" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert step.get("id") == "history_gate"


def test_130_atlas_doctor_history_gate_fail_step_referans() -> None:
    """Fail step `rc_hist != '0'` kontrolü içerir."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    fail_step = next(
        (s for s in steps
         if "fail the workflow" in s.get("name", "").lower()),
        None,
    )
    assert fail_step is not None
    cond = fail_step.get("if", "")
    assert "history_gate.outputs.rc_hist" in cond


def test_130_atlas_doctor_history_gate_artifact() -> None:
    """Upload artifact listesinde `doctor-history-strict.txt`."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert "doctor-history-strict.txt" in path_str


def test_100_atlas_doctor_mevcut_2_artifact_dokunulmadi() -> None:
    """SPEC 070 mevcut 2 artifact (`doctor-report.json`, `doctor-diff.txt`)
    upload listesinde AYNI (BİT-UYUMLU)."""
    data = _load("atlas-doctor.yml")
    steps = data["jobs"]["doctor"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert "doctor-report.json" in path_str
    assert "doctor-diff.txt" in path_str


# ═════════════════════════════════════════════════════════════════════
# SPEC 107 — atlas-vault.yml scheduled backup + split
# ═════════════════════════════════════════════════════════════════════


def test_107_atlas_vault_yaml_valid() -> None:
    data = _load("atlas-vault.yml")
    assert isinstance(data, dict)
    assert data.get("name") == "atlas-vault"


def test_107_atlas_vault_schedule_daily() -> None:
    """cron: her gün 03:00 UTC."""
    data = _load("atlas-vault.yml")
    on = data.get("on") or data.get(True)
    assert isinstance(on, dict)
    assert "schedule" in on
    crons = on["schedule"]
    assert isinstance(crons, list) and len(crons) >= 1
    assert any(c.get("cron") == "0 3 * * *" for c in crons)


def test_107_atlas_vault_workflow_dispatch() -> None:
    data = _load("atlas-vault.yml")
    on = data.get("on") or data.get(True)
    assert "workflow_dispatch" in on


def test_107_atlas_vault_permissions() -> None:
    data = _load("atlas-vault.yml")
    perms = data.get("permissions", {})
    assert perms.get("contents") == "read"


def test_107_atlas_vault_backup_command() -> None:
    """Job `atlas vault backup --auto --split 50 --keep 7` çalıştırır."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "atlas vault backup" in run_blocks
    assert "--auto" in run_blocks
    assert "--split 50" in run_blocks
    assert "--keep 7" in run_blocks


def test_107_atlas_vault_check_exists() -> None:
    """`vault/` yoksa skip → workflow durmaz."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    check_step = next(
        (s for s in steps if "check vault" in s.get("name", "").lower()),
        None,
    )
    assert check_step is not None
    assert "has_vault" in check_step.get("run", "")


def test_107_atlas_vault_upload_artifact_conditional() -> None:
    """Upload artifact yalnız has_vault=true iken."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    assert "has_vault" in upload_step.get("if", "")
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert "vault-*.tar.gz." in path_str


def test_107_atlas_vault_readme_badge_row() -> None:
    """README ci-status bloğunda `atlas-vault` satırı var."""
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    assert "atlas-vault.yml" in readme
    assert "| atlas-vault |" in readme


# ═════════════════════════════════════════════════════════════════════
# SPEC 112 — atlas-vault.yml restore-verify step
# ═════════════════════════════════════════════════════════════════════


def test_112_atlas_vault_restore_verify_step() -> None:
    """`Restore + verify (integrity check, SPEC 112)` step'i var."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps
         if "restore + verify" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "atlas vault restore" in run
    assert "--split --apply" in run
    assert "atlas vault verify" in run
    assert "--strict" in run


def test_112_atlas_vault_restore_verify_conditional() -> None:
    """Step yalnız has_vault=true iken çalışır."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps
         if "restore + verify" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    cond = step.get("if", "")
    assert "has_vault" in cond


def test_112_atlas_vault_restore_verify_fail_fast() -> None:
    """`set -e` ile ilk hata anında fail."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps
         if "restore + verify" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "set -e" in run


# ═════════════════════════════════════════════════════════════════════
# SPEC 113 — atlas-metrics.yml gzip artifact entegrasyonu
# ═════════════════════════════════════════════════════════════════════


def test_113_atlas_metrics_group_prom_gzip_step() -> None:
    """`Generate group prometheus (gzip, SPEC 103/113)` step'i var."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    step = next(
        (s for s in steps
         if "group prometheus" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "--group-by day" in run
    assert "--format prometheus" in run
    assert "--gzip" in run
    assert "metrics-group-day.prom" in run


def test_113_atlas_metrics_group_prom_conditional() -> None:
    """Step yalnız has_data=true iken."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    step = next(
        (s for s in steps
         if "group prometheus" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    cond = step.get("if", "")
    assert "has_data" in cond


def test_113_atlas_metrics_gzip_artifact_uploaded() -> None:
    """Upload artifact listesinde `metrics-group-day.prom.gz` var."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert "metrics-group-day.prom.gz" in path_str


# ═════════════════════════════════════════════════════════════════════
# SPEC 131 — atlas-metrics.yml alert-webhook post
# ═════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════════════
# SPEC 137 — atlas-metrics.yml alert-history artifact
# ═════════════════════════════════════════════════════════════════════


def test_137_atlas_metrics_alert_history_artifact() -> None:
    """Upload artifact listesinde `.atlas/alert-history.jsonl`."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    assert ".atlas/alert-history.jsonl" in path_str


def test_137_atlas_metrics_if_no_files_found_ignore() -> None:
    """`if-no-files-found: ignore` — dosya yoksa hata yok."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    with_block = upload_step.get("with", {})
    assert with_block.get("if-no-files-found") == "ignore"


def test_131_atlas_metrics_alert_webhook_step() -> None:
    """`Post alert webhook (SPEC 064/131)` step var."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    step = next(
        (s for s in steps
         if "alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "atlas metrics" in run
    assert "--alert 30" in run
    assert "--alert-webhook" in run


def test_131_atlas_metrics_alert_webhook_env_secret() -> None:
    """Env `ALERT_WEBHOOK_URL` GitHub secret'tan gelir."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    step = next(
        (s for s in steps
         if "alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    env = step.get("env", {})
    val = env.get("ALERT_WEBHOOK_URL", "")
    assert "secrets" in val
    assert "ATLAS_ALERT_WEBHOOK_URL" in val


def test_131_atlas_metrics_alert_webhook_conditional() -> None:
    """Step yalnız has_data + env != '' iken."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    step = next(
        (s for s in steps
         if "alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    cond = step.get("if", "")
    assert "has_data" in cond
    assert "ALERT_WEBHOOK_URL" in cond


def test_131_atlas_metrics_alert_webhook_continue_on_error() -> None:
    """Webhook POST fail → job kırılmaz."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    step = next(
        (s for s in steps
         if "alert webhook" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert step.get("continue-on-error") is True


def test_113_atlas_metrics_mevcut_4_artifact_dokunulmadi() -> None:
    """SPEC 074/095 mevcut 4 artifact listede AYNI."""
    data = _load("atlas-metrics.yml")
    steps = data["jobs"]["metrics"]["steps"]
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    path_str = str(upload_step.get("with", {}).get("path", ""))
    for name in ("metrics-human.txt", "metrics.json", "metrics.prom",
                 "metrics-cost-by-day.json"):
        assert name in path_str


# ═════════════════════════════════════════════════════════════════════
# SPEC 117 — atlas-vault.yml doctor gate on restored vault
# ═════════════════════════════════════════════════════════════════════


def test_117_atlas_vault_doctor_gate_step() -> None:
    """`Doctor gate on restored vault (SPEC 117)` step var."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps if "doctor gate" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "atlas doctor" in run
    assert "--strict" in run
    assert "--scan-src" in run


def test_117_atlas_vault_doctor_gate_env() -> None:
    """Doctor gate ATLAS_VAULT env = /tmp/verify-vault."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps if "doctor gate" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    env = step.get("env", {})
    assert env.get("ATLAS_VAULT") == "/tmp/verify-vault"


def test_117_atlas_vault_doctor_gate_conditional() -> None:
    """Step yalnız has_vault=true iken."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps if "doctor gate" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert "has_vault" in step.get("if", "")


# ═════════════════════════════════════════════════════════════════════
# SPEC 124 — atlas-vault.yml retention verify step
# ═════════════════════════════════════════════════════════════════════


def test_124_atlas_vault_retention_verify_step() -> None:
    """`Verify retention (--keep 7, SPEC 041.1/124)` step var."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps if "verify retention" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "vault-*.tar.gz.*" in run
    assert "wc -l" in run


def test_124_atlas_vault_retention_conditional() -> None:
    """Retention step has_vault=true conditional."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps if "verify retention" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert "has_vault" in step.get("if", "")


def test_124_atlas_vault_retention_fail_fast() -> None:
    """set -e fail-fast + `::error::` marker."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps if "verify retention" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    run = step.get("run", "")
    assert "set -e" in run
    assert "::error::" in run


def test_117_atlas_vault_doctor_gate_fail_fast() -> None:
    """`set -e` fail-fast."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    step = next(
        (s for s in steps if "doctor gate" in s.get("name", "").lower()),
        None,
    )
    assert step is not None
    assert "set -e" in step.get("run", "")


def test_112_atlas_vault_mevcut_stepler_dokunulmadi() -> None:
    """SPEC 107 mevcut backup + upload step'leri korundu."""
    data = _load("atlas-vault.yml")
    steps = data["jobs"]["backup"]["steps"]
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "atlas vault backup --auto --split 50 --keep 7" in run_blocks
    upload_step = next(
        (s for s in steps
         if s.get("uses", "").startswith("actions/upload-artifact")),
        None,
    )
    assert upload_step is not None
    assert "vault-*.tar.gz." in str(upload_step["with"]["path"])

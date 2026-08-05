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


def test_089_atlas_ci_status_readme_badge_row() -> None:
    """README ci-status bloğunda `atlas-ci-status` satırı var."""
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    assert "atlas-ci-status.yml" in readme
    assert "| atlas-ci-status |" in readme

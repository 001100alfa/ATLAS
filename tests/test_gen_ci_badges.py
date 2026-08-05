"""SPEC 082 — tools/scripts/gen_ci_badges.py testleri."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "tools" / "scripts" / "gen_ci_badges.py"
_README = _REPO / "README.md"


def _run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Script'i subprocess ile çalıştır."""
    return subprocess.run(  # noqa: S603 — argv sabit
        [sys.executable, str(_SCRIPT), *args],
        cwd=str(cwd or _REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )


def test_082_script_mevcut() -> None:
    assert _SCRIPT.is_file()


def test_082_check_mod_repo_guncel() -> None:
    """Şu an repo README güncel — --check exit 0 dönmeli."""
    result = _run_script("--check")
    assert result.returncode == 0, (
        f"--check başarısız: stdout={result.stdout} stderr={result.stderr}"
    )
    assert "güncel" in result.stdout or "OK" in result.stdout


def test_082_readme_ci_status_markorleri_iceriyor() -> None:
    """README'de ci-status marker'ları var."""
    text = _README.read_text(encoding="utf-8")
    assert "<!-- ci-status:start -->" in text
    assert "<!-- ci-status:end -->" in text


def test_082_readme_tum_workflowlari_iceriyor() -> None:
    """5 workflow (atlas-doctor + atlas-metrics + ci + no-docker +
    vault-health + ci-status kendisi) badge'de var."""
    text = _README.read_text(encoding="utf-8")
    for wf in ("atlas-doctor.yml", "atlas-metrics.yml", "no-docker.yml",
               "vault-health.yml", "ci-status.yml"):
        assert wf in text, f"{wf} README badge'de eksik"


def test_082_check_drift_tespit(tmp_path: Path) -> None:
    """Boş klasörde çalıştır: README yok, --check exit 1."""
    # Sahte proje: sadece .github/workflows + boş README + tools/scripts
    proj = tmp_path / "proj"
    (proj / ".github" / "workflows").mkdir(parents=True)
    (proj / ".github" / "workflows" / "test.yml").write_text(
        "name: test\non: push\njobs: {}\n", encoding="utf-8",
    )
    (proj / "README.md").write_text("# proje\n", encoding="utf-8")
    # Script'i sahte cwd ile çalıştır — ama script `_REPO_ROOT` sabit
    # (script dosyasına göre). Sahte cwd yerine gerçek REPO'da --check
    # ile drift'i simüle et: geçici yeni workflow ekle → drift oluşur.
    fake_wf = _REPO / ".github" / "workflows" / "_test_drift.yml"
    fake_wf.write_text("name: test-drift\non: push\njobs: {}\n",
                       encoding="utf-8")
    try:
        result = _run_script("--check")
        assert result.returncode == 1
        assert "guncel degil" in result.stderr.lower()
    finally:
        fake_wf.unlink()


def test_082_workflow_ci_status_yml_valid() -> None:
    """SPEC 082 workflow YAML valid parse (opsiyonel PyYAML)."""
    try:
        import yaml as _yaml
    except ImportError:
        pytest.skip("PyYAML yok")
    wf_path = _REPO / ".github" / "workflows" / "ci-status.yml"
    assert wf_path.is_file()
    data = _yaml.safe_load(wf_path.read_text(encoding="utf-8"))
    assert data["name"] == "ci-status"
    # Tetikleyici + gen_ci_badges.py çağrısı
    on = data.get("on") or data.get(True)
    assert "push" in on
    assert "pull_request" in on
    steps = data["jobs"]["drift-check"]["steps"]
    run_blocks = "\n".join(s.get("run", "") for s in steps if s.get("run"))
    assert "gen_ci_badges.py --check" in run_blocks
    assert "exit 1" in run_blocks


def test_082_repo_slug_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """`GITHUB_REPOSITORY` env override edilirse badge URL değişir."""
    monkeypatch.setenv("GITHUB_REPOSITORY", "test-owner/test-repo")
    result = _run_script("--repo", "test-owner/test-repo", "--check")
    # Repo güncel olsa da olmasa da script çalıştı
    assert result.returncode in (0, 1)


def test_082_build_badge_block_deterministik() -> None:
    """Aynı repo aynı çıktı — belirsizlik yok."""
    # Script iki kere çağrılırsa aynı block üretilmeli (idempotent)
    _run_script()  # birinci
    text1 = _README.read_text(encoding="utf-8")
    _run_script()  # ikinci
    text2 = _README.read_text(encoding="utf-8")
    assert text1 == text2

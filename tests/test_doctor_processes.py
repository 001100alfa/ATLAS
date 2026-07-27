"""Artık süreç tespiti ve temizliği.

Gerçek süreç başlatmaz: süreç listesi taklit edilir. Korunan davranış — kapsam
DAR olmalı. Bu denetim `taskkill` çalıştırıyor; depo dışındaki bir süreci
yanlışlıkla listeye alması, kullanıcının başka bir işini kapatması demektir.
"""

from __future__ import annotations

from pathlib import Path

from tools.doctor_gui import processes


def _fake_procs(monkeypatch, rows: list[dict]) -> None:
    monkeypatch.setattr(processes, "_all_processes", lambda: rows)


def _repo(tmp_path: Path) -> Path:
    """Ajan ikilileri gerçekten var olan küçük bir depo iskeleti."""
    goose = tmp_path / "tools" / "goose" / "goose-package"
    goose.mkdir(parents=True)
    (goose / "goose.exe").write_text("x", encoding="utf-8")
    cline = tmp_path / "tools" / "ai-cli" / "node_modules" / "cline" / "bin"
    cline.mkdir(parents=True)
    (cline / "cline").write_text("x", encoding="utf-8")
    return tmp_path


def test_repo_agent_process_is_stray(tmp_path: Path, monkeypatch):
    root = _repo(tmp_path)
    exe = str(root / "tools" / "goose" / "goose-package" / "goose.exe")
    _fake_procs(monkeypatch, [{"ProcessId": 111, "Name": "goose.exe", "ExecutablePath": exe}])
    found = processes.stray(root)
    assert [p["pid"] for p in found] == [111]


def test_outside_repo_is_never_touched(tmp_path: Path, monkeypatch):
    """Kapsam darlığı: başka bir kurulumun ajanı listeye GİRMEZ."""
    root = _repo(tmp_path)
    _fake_procs(
        monkeypatch,
        [
            {"ProcessId": 1, "Name": "goose.exe", "ExecutablePath": r"C:\Baska\juggler\goose.exe"},
            {"ProcessId": 2, "Name": "node.exe", "ExecutablePath": r"C:\Program Files\node.exe"},
            {"ProcessId": 3, "Name": "ollama.exe", "ExecutablePath": r"C:\Ollama\ollama.exe"},
        ],
    )
    assert processes.stray(root) == []


def test_panel_open_suspends_detection(tmp_path: Path, monkeypatch):
    """Panel açıkken ajanlar kullanımda olabilir — hiçbir şey artık sayılmaz."""
    root = _repo(tmp_path)
    exe = str(root / "tools" / "goose" / "goose-package" / "goose.exe")
    _fake_procs(
        monkeypatch,
        [
            {"ProcessId": 9, "Name": "juggler.exe", "ExecutablePath": r"C:\x\juggler.exe"},
            {"ProcessId": 111, "Name": "goose.exe", "ExecutablePath": exe},
        ],
    )
    assert processes.juggler_running(root) is True
    assert processes.stray(root) == []


def test_sibling_helper_binary_counts(tmp_path: Path, monkeypatch):
    """Ajanın yanındaki yardımcı ikili de aynı kurulumun parçasıdır (cline gibi)."""
    root = _repo(tmp_path)
    helper = str(root / "tools" / "ai-cli" / "node_modules" / "cline" / "bin" / "cline-win.exe")
    _fake_procs(monkeypatch, [{"ProcessId": 7, "Name": "cline.exe", "ExecutablePath": helper}])
    assert [p["pid"] for p in processes.stray(root)] == [7]


def test_own_process_excluded(tmp_path: Path, monkeypatch):
    """Sihirbazın kendi süreci asla listeye girmez."""
    import os

    root = _repo(tmp_path)
    exe = str(root / "tools" / "goose" / "goose-package" / "goose.exe")
    _fake_procs(monkeypatch, [{"ProcessId": os.getpid(), "Name": "x", "ExecutablePath": exe}])
    assert processes.stray(root) == []


def test_kill_counts_already_dead_as_gone(monkeypatch):
    """Alt süreçler üst süreçle birlikte ölür; bu başarısızlık değildir."""
    calls = []

    class R:
        def __init__(self, code: int, out: str):
            self.returncode, self.stdout, self.stderr = code, out, ""

    def fake_run(argv, **kw):
        pid = argv[-1]
        calls.append(pid)
        if pid == "1":
            return R(0, "SUCCESS")
        if pid == "2":
            return R(128, 'ERROR: The process "2" not found.')
        return R(1, "Access denied")

    monkeypatch.setattr(processes.subprocess, "run", fake_run)
    res = processes.kill([1, 2, 3])
    assert res["killed"] == [1]
    assert res["gone"] == [2]
    assert len(res["failed"]) == 1 and res["failed"][0].startswith("3:")


def test_no_processes_when_listing_fails(tmp_path: Path, monkeypatch):
    """Süreç listesi alınamazsa sessizce boş döner — yanlış pozitif üretmez."""
    root = _repo(tmp_path)
    _fake_procs(monkeypatch, [])
    assert processes.stray(root) == []

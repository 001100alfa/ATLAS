"""SPEC 003.1 — ACP (subprocess ACP-lite) planner testleri.

Gerçek subprocess YOK: `subprocess.Popen` monkeypatch edilir.
`_FakePopen` sınıfı JSON-RPC yanıtlarını script'lenmiş bir sırayla
döndürür; stdin.write yakalanır; kill/wait kaydedilir.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from atlas_core.orchestrator import planner as planner_mod
from atlas_core.orchestrator.goals import Goal
from atlas_core.orchestrator.planner import LLMPlannerError, make_planner


def _goal_llm() -> Goal:
    return Goal(
        goal="dosya yaz",
        plan_kind="llm",
        plan_steps=(),
        action_allowlist=frozenset({"write"}),
        shell_allow_regex=None,
        judge_kind="file_exists",
        judge_arg="out.txt",
        budget=20.0,
        max_steps=3,
        costs={"read": 1.0, "write": 2.0, "shell": 5.0},
    )


class _FakeStdout:
    """Script'lenmiş satırlar; hepsi tükenirse `""` (EOF) döner."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = list(lines)

    def readline(self) -> str:
        if not self._lines:
            return ""
        return self._lines.pop(0)


class _FakePopen:
    """`subprocess.Popen` yerine geçen minimal sahte.

    `stdout_lines`: readline sırasıyla döndürülecek satırlar (\n dahil).
    `stderr_text`: stderr.read() cevabı.
    `wait_raises`: True verilirse ilk wait TimeoutExpired atar.
    `returncode`: wait/poll cevabı için.
    """

    def __init__(
        self,
        stdout_lines: list[str],
        *,
        stderr_text: str = "",
        wait_raises: bool = False,
        returncode: int = 0,
    ) -> None:
        self.stdin = io.StringIO()
        self.stdin.close = self._close_stdin  # type: ignore[method-assign]
        self._stdin_closed = False
        self.stdout = _FakeStdout(stdout_lines)
        self.stderr = io.StringIO(stderr_text)
        self._wait_raises = wait_raises
        self._wait_called = 0
        self.kill_called = False
        self.returncode: int | None = None
        self._final_rc = returncode
        self.args = []  # type: ignore[assignment]

    # subprocess.Popen ile uyumlu API'ler
    def _close_stdin(self) -> None:
        self._stdin_closed = True

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self._wait_called += 1
        if self._wait_raises and self._wait_called == 1:
            raise subprocess.TimeoutExpired(cmd="acp", timeout=timeout or 0)
        self.returncode = self._final_rc
        return self._final_rc

    def kill(self) -> None:
        self.kill_called = True
        self.returncode = -9

    # Yardımcı — stdin'e yazılanı JSON satır listesi olarak döner
    def stdin_messages(self) -> list[dict[str, Any]]:
        text = self.stdin.getvalue()
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def _prep_bin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    fake = tmp_path / "fake-acp-agent"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("ATLAS_LLM", "acp")
    monkeypatch.setenv("ATLAS_LLM_ACP_BIN", str(fake))
    return fake


def _rpc(id_: int, result: dict[str, Any] | None = None,
         error: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result or {}
    return json.dumps(payload) + "\n"


def _notif_agent_chunk(session_id: str, text: str) -> str:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": text},
                },
            },
        }
    ) + "\n"


# ---------- AC12: fabrika (bin var) ----------

def test_fabrika_bin_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    p = make_planner(_goal_llm())
    assert callable(p)


def test_fabrika_bin_which(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_LLM", "acp")
    monkeypatch.delenv("ATLAS_LLM_ACP_BIN", raising=False)
    fake = tmp_path / "acp-in-path"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setattr(planner_mod.shutil, "which", lambda _n: str(fake))
    p = make_planner(_goal_llm())
    assert callable(p)


# ---------- AC13: bin yok = fabrika anında ----------

def test_bin_yok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM", "acp")
    monkeypatch.delenv("ATLAS_LLM_ACP_BIN", raising=False)
    monkeypatch.setattr(planner_mod.shutil, "which", lambda _n: None)
    with pytest.raises(LLMPlannerError, match="acp agent bin bulunamadı"):
        make_planner(_goal_llm())


def test_bin_env_yanlis(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATLAS_LLM", "acp")
    monkeypatch.setenv("ATLAS_LLM_ACP_BIN", str(tmp_path / "yok.exe"))
    with pytest.raises(LLMPlannerError, match="dosya değil"):
        make_planner(_goal_llm())


# ---------- AC14: happy call ----------

def test_call_happy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    sid = "sess-42"
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": sid}),
        _notif_agent_chunk(sid, "write:x.txt:"),
        _notif_agent_chunk(sid, "1"),  # iki parçalı geldi
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    assert p("goal", []) == "write:x.txt:1"

    # stdin sözleşmesi: 3 istek gönderildi
    msgs = fake.stdin_messages()
    assert len(msgs) == 3
    assert msgs[0]["method"] == "initialize"
    assert msgs[1]["method"] == "session/new"
    assert msgs[2]["method"] == "session/prompt"
    assert msgs[2]["params"]["sessionId"] == sid
    # prompt gövdesi
    prompt_content = msgs[2]["params"]["prompt"][0]
    assert prompt_content["type"] == "text"
    assert "dosya yaz" in prompt_content["text"]


# ---------- AC15: JSON-RPC error (initialize) ----------

def test_call_init_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [_rpc(1, error={"code": -1, "message": "unauthorized"})]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"initialize.*unauthorized"):
        p("g", [])


def test_call_session_new_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, error={"code": -2, "message": "session limit"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"session/new.*session limit"):
        p("g", [])


def test_call_prompt_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _rpc(3, error={"code": -3, "message": "model overloaded"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"session/prompt.*model overloaded"):
        p("g", [])


# ---------- AC16: timeout ----------

def test_call_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM_TIMEOUT", "1")
    # readline hiç satır dönmüyor — deadline aşınca TimeoutError.
    # `time.monotonic` monkeypatch ile deadline hemen aşılır.
    _prep_bin(monkeypatch, tmp_path)
    lines: list[str] = []  # boş
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    times = iter([0.0, 100.0])  # başlangıç anı 0, sonraki 100 → 1s aşıldı
    monkeypatch.setattr(planner_mod.time, "monotonic", lambda: next(times))

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"timeout"):
        p("g", [])
    # süreç temizlenmiş olmalı (wait çağrıldı)
    assert fake._wait_called >= 1


# ---------- AC17: erken exit ----------

def test_call_erken_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    # readline hemen "" döner (EOF); subprocess exit=2.
    fake = _FakePopen([], stderr_text="agent crashed", returncode=2)
    fake.returncode = 2  # poll() 2 döner
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"exit=2.*agent crashed"):
        p("g", [])


# ---------- AC18: boş yanıt ----------

def test_call_bos_yanit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _rpc(3, {"stopReason": "end_turn"}),  # hiç chunk gelmedi
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"boş plan"):
        p("g", [])


# ---------- AC19: UTF-8 ----------

def test_call_utf8(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _notif_agent_chunk("s1", "write:çıkış.txt:🚀"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    assert p("g", []) == "write:çıkış.txt:🚀"


# ---------- AC20: context 006 injection ----------

def test_006_context_injection(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    ctx = "## GBrain\n- [[hello]]: merhaba"
    p = make_planner(_goal_llm(), context=ctx)
    p("g", [])

    msgs = fake.stdin_messages()
    prompt_text = msgs[2]["params"]["prompt"][0]["text"]
    assert "Önceden bilinen bağlam (GBrain):" in prompt_text
    assert "[[hello]]" in prompt_text


# ---------- Ek: geçersiz JSON satır ----------

def test_call_gecersiz_json_satir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        "bu geçerli JSON değil\n",
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"geçersiz JSON"):
        p("g", [])


# ---------- Ek: Popen OSError (bin başlatılamadı) ----------

def test_call_popen_oserror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)

    def fake_popen(*_a: Any, **_kw: Any) -> _FakePopen:
        raise OSError("permission denied")

    monkeypatch.setattr(planner_mod.subprocess, "Popen", fake_popen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"başlatılamadı.*permission denied"):
        p("g", [])


# ---------- Ek: teardown süreç sızıntısı yasak ----------

def test_teardown_wait_takilirsa_kill(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _prep_bin(monkeypatch, tmp_path)
    sid = "s1"
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": sid}),
        _notif_agent_chunk(sid, "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines, wait_raises=True, returncode=0)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    assert p("g", []) == "write:x.txt:1"
    # wait ilk seferde TimeoutExpired → kill devreye girmeli
    assert fake.kill_called is True


# ---------- SPEC 016: tool_call açık red ----------


def _notif_tool_call(session_id: str, tool_name: str) -> str:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "tool_call",
                    "title": tool_name,
                    "toolCall": {"name": tool_name, "input": {}},
                },
            },
        }
    ) + "\n"


def _notif_tool_call_update(session_id: str, tool_name: str) -> str:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "tool_call_update",
                    "toolCall": {"name": tool_name, "status": "in_progress"},
                },
            },
        }
    ) + "\n"


def test_016_tool_call_acik_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SPEC 016: agent tool_call gönderirse LLMPlannerError."""
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _notif_tool_call("s1", "read_file"),
        # buradan sonra ulaşılmıyor
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"tool-use şu an desteklenmiyor"):
        p("g", [])
    # Süreç kill'lenmiş olmalı (teardown wait+kill)
    assert fake._wait_called >= 1


def test_016_tool_call_update_acik_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _notif_tool_call_update("s1", "shell"),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"tool-use şu an desteklenmiyor"):
        p("g", [])


def test_016_bilinmeyen_session_update_yok_sayilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Bilinmeyen sessionUpdate (ör. plan_update) sessizce atlanır — regresyon."""
    _prep_bin(monkeypatch, tmp_path)
    unknown_notif = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": "s1",
                "update": {"sessionUpdate": "plan_update", "some": "data"},
            },
        }
    ) + "\n"
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        unknown_notif,  # sessizce atlanmalı
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    assert p("g", []) == "write:x.txt:1"  # bilinmeyen notif atlandı


# ---------- SPEC 016.1: fs/read_text_file minimum ----------


def _client_request(method: str, params: dict[str, Any], req_id: int = 100) -> str:
    """Agent → client JSON-RPC request (method + id)."""
    return json.dumps(
        {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    ) + "\n"


def test_016_1_fs_read_happy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Happy path: agent fs/read_text_file, client gerçek içerik döner."""
    monkeypatch.chdir(tmp_path)  # proje kökü = tmp_path
    _prep_bin(monkeypatch, tmp_path)
    target = tmp_path / "notlar.md"
    target.write_text("içerik satırı 1\nsatır 2\n", encoding="utf-8")

    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _client_request("fs/read_text_file", {"path": str(target)}, req_id=100),
        # sonra agent normal cevap üretsin
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    assert p("g", []) == "write:x.txt:1"

    msgs = fake.stdin_messages()
    # 3 istek (initialize, session/new, session/prompt) + 1 cevap (id=100)
    responses = [m for m in msgs if m.get("id") == 100]
    assert len(responses) == 1
    result = responses[0]["result"]
    assert "içerik satırı" in result["content"]


def test_016_1_fs_read_yol_traversal_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Yol proje kökü dışına çıkarsa permission denied."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)

    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _client_request(
            "fs/read_text_file",
            {"path": str(tmp_path.parent / "otherfile.txt")},
            req_id=100,
        ),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])

    msgs = fake.stdin_messages()
    responses = [m for m in msgs if m.get("id") == 100]
    assert len(responses) == 1
    err = responses[0]["error"]
    assert err["code"] == -32000
    assert "permission denied" in err["message"]


def test_016_1_fs_read_dosya_yok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Dosya yoksa file not found error."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)

    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _client_request(
            "fs/read_text_file",
            {"path": str(tmp_path / "yok.md")},
            req_id=100,
        ),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])

    msgs = fake.stdin_messages()
    err = next(m for m in msgs if m.get("id") == 100)["error"]
    assert err["code"] == -32000
    assert "file not found" in err["message"]


def test_016_1_fs_write_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Yazma metodu red edilir: -32000 not supported."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)

    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _client_request(
            "fs/write_text_file",
            {"path": str(tmp_path / "x.txt"), "content": "z"},
            req_id=100,
        ),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])

    msgs = fake.stdin_messages()
    err = next(m for m in msgs if m.get("id") == 100)["error"]
    assert err["code"] == -32000
    assert "not supported" in err["message"]
    assert "fs/write_text_file" in err["message"]


def test_016_1_bilinmeyen_method_32601(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Bilinmeyen method: JSON-RPC -32601 Method not found."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)

    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _client_request("banana/split", {}, req_id=100),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])

    msgs = fake.stdin_messages()
    err = next(m for m in msgs if m.get("id") == 100)["error"]
    assert err["code"] == -32601
    assert "banana/split" in err["message"]


def test_016_1_tool_call_notif_hala_red(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SPEC 016 tool_call notification hala LLMPlannerError — 016.1 request
    yolu ile karışmaz."""
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _notif_tool_call("s1", "read_file"),  # id YOK → notification → 016 red
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"tool-use şu an desteklenmiyor"):
        p("g", [])


# ---------- SPEC 016.2: session/request_permission ----------


def _perm_request(
    tool_name: str, options: list[dict[str, str]] | None = None, req_id: int = 200
) -> str:
    params: dict[str, Any] = {
        "toolCall": {"name": tool_name, "input": {}},
    }
    if options is not None:
        params["options"] = options
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "session/request_permission",
            "params": params,
        }
    ) + "\n"


def test_016_2_read_tool_allow_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Read-only tool → allow_once."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _perm_request("fs/read_text_file", options=[
            {"optionId": "allow_once", "kind": "allow_once", "name": "İzin ver"},
            {"optionId": "reject", "kind": "reject", "name": "Reddet"},
        ]),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])
    msgs = fake.stdin_messages()
    resp = next(m for m in msgs if m.get("id") == 200)
    assert resp["result"]["outcome"]["outcome"] == "selected"
    assert resp["result"]["outcome"]["optionId"] == "allow_once"


def test_016_2_write_tool_reject(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Write tool → reject."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _perm_request("fs/write_text_file", options=[
            {"optionId": "allow_once", "kind": "allow_once", "name": "OK"},
            {"optionId": "reject", "kind": "reject", "name": "No"},
        ]),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])
    msgs = fake.stdin_messages()
    resp = next(m for m in msgs if m.get("id") == 200)
    assert resp["result"]["outcome"]["optionId"] == "reject"


def test_016_2_bilinmeyen_tool_reject(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Bilinmeyen tool → reject (savunmalı varsayılan)."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _perm_request("mystery/tool", options=None),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])
    msgs = fake.stdin_messages()
    resp = next(m for m in msgs if m.get("id") == 200)
    assert resp["result"]["outcome"]["optionId"] == "reject"


def test_016_2_options_yoksa_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """options verilmemişse fallback string kullanılır."""
    monkeypatch.chdir(tmp_path)
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _perm_request("fs/read_text_file", options=None),  # options yok
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    p = make_planner(_goal_llm())
    p("g", [])
    msgs = fake.stdin_messages()
    resp = next(m for m in msgs if m.get("id") == 200)
    # options yok → sabit fallback "allow_once"
    assert resp["result"]["outcome"]["optionId"] == "allow_once"


# ---------- SPEC 003.2: özel llm_prompt acp session/prompt gövdesinde ----------

def test_003_2_ozel_prompt_prompt_de_gorunur(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC10: llm_prompt acp session/prompt request'inde prompt[0].text'te geçer."""
    _prep_bin(monkeypatch, tmp_path)
    lines = [
        _rpc(1, {"protocolVersion": 1}),
        _rpc(2, {"sessionId": "s1"}),
        _notif_agent_chunk("s1", "write:x.txt:1"),
        _rpc(3, {"stopReason": "end_turn"}),
    ]
    fake = _FakePopen(lines)
    monkeypatch.setattr(planner_mod.subprocess, "Popen", lambda *a, **kw: fake)

    from dataclasses import replace
    g = replace(_goal_llm(), llm_prompt="ROLE: yapı mühendisi")
    p = make_planner(g)
    p("g", [])
    msgs = fake.stdin_messages()
    prompt_text = msgs[2]["params"]["prompt"][0]["text"]
    assert prompt_text.startswith("ROLE: yapı mühendisi")
    assert "Görev: dosya yaz" in prompt_text
    assert "TEK SATIRLIK" in prompt_text
    assert "planlama alt-ajansısın" not in prompt_text


# ---------- Ek: ATLAS_LLM_ACP_ARGS ekstra argv ----------

def test_extra_argv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _prep_bin(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_LLM_ACP_ARGS", "--role planner --json")
    captured: dict[str, Any] = {}

    def fake_popen(argv: list[str], **_kw: Any) -> _FakePopen:
        captured["argv"] = argv
        fake = _FakePopen(
            [
                _rpc(1, {"protocolVersion": 1}),
                _rpc(2, {"sessionId": "s1"}),
                _notif_agent_chunk("s1", "write:x.txt:1"),
                _rpc(3, {"stopReason": "end_turn"}),
            ]
        )
        return fake

    monkeypatch.setattr(planner_mod.subprocess, "Popen", fake_popen)
    p = make_planner(_goal_llm())
    p("g", [])
    assert captured["argv"][-3:] == ["--role", "planner", "--json"]

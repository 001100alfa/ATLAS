"""SPEC 003.1 — Anthropic Messages API planner testleri.

Ağ YOK: `urllib.request.urlopen` monkeypatch edilir. API key stderr'a
sızmamalı (AC24 — implicit; hiçbir hata mesajı `x-api-key` içermez).
"""

from __future__ import annotations

import io
import json
from typing import Any
from urllib import error as urllib_error

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


class _FakeResponse:
    """`urlopen` context manager sahtesi — `read()` bayt döner."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_a: Any) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _prep_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-KEY-do-not-log")


# ---------- AC1: fabrika (env dolu) ----------

def test_fabrika_env_dolu(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)
    p = make_planner(_goal_llm())
    assert callable(p)


# ---------- AC2: key yok = fabrika anında ----------

def test_key_yok_fabrika_hata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LLMPlannerError, match="ANTHROPIC_API_KEY"):
        make_planner(_goal_llm())


def test_key_bosluk_fabrika_hata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
    with pytest.raises(LLMPlannerError, match="ANTHROPIC_API_KEY"):
        make_planner(_goal_llm())


# ---------- AC3: happy call ----------

def test_call_happy(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, timeout: int = 0) -> _FakeResponse:
        seen["url"] = req.full_url
        seen["headers"] = {k.lower(): v for k, v in req.header_items()}
        seen["body"] = json.loads(req.data.decode("utf-8"))
        seen["timeout"] = timeout
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1\n"}],
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    assert p("goal", []) == "write:x.txt:1"
    # Header sözleşmesi
    assert seen["headers"]["x-api-key"] == "sk-test-KEY-do-not-log"
    assert seen["headers"]["anthropic-version"] == "2023-06-01"
    # URL varsayılan
    assert "api.anthropic.com" in seen["url"]
    # Model + prompt
    body = seen["body"]
    assert "claude-3-5-sonnet-latest" == body["model"]
    assert body["messages"][0]["role"] == "user"
    assert "dosya yaz" in body["messages"][0]["content"]


# ---------- AC4: timeout ----------

def test_call_timeout_via_urlerror(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_TIMEOUT", "5")

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise urllib_error.URLError(TimeoutError("read"))

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"timeout: 5s"):
        p("g", [])


def test_call_timeout_direct(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_TIMEOUT", "7")

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise TimeoutError("read")

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"timeout: 7s"):
        p("g", [])


def test_call_socket_timeout_via_urlerror(monkeypatch: pytest.MonkeyPatch) -> None:
    # `socket.timeout` Py3.10+ TimeoutError aliası; URLError'a sarılı gelebilir.
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise urllib_error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match=r"timeout"):
        p("g", [])


# ---------- AC5: HTTPError ----------

def test_call_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise urllib_error.HTTPError(
            url="https://api.anthropic.com/v1/messages",
            code=429,
            msg="Too Many Requests",
            hdrs=None,  # type: ignore[arg-type]
            fp=io.BytesIO(b"rate limit exceeded"),
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError) as exc_info:
        p("g", [])
    msg = str(exc_info.value)
    assert "HTTP 429" in msg
    assert "rate limit" in msg


# ---------- AC6: URLError (ağ) ----------

def test_call_urlerror_agv(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise urllib_error.URLError("Name or service not known")

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError) as exc_info:
        p("g", [])
    msg = str(exc_info.value)
    assert "başlatılamadı" in msg
    assert "Name or service" in msg


# ---------- AC7: geçersiz JSON ----------

def test_call_gecersiz_json(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(b"<html>500 internal error</html>")

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match="geçersiz JSON"):
        p("g", [])


# ---------- AC8: boş içerik ----------

def test_call_bos_icerik(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(json.dumps({"content": []}).encode("utf-8"))

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match="boş plan"):
        p("g", [])


def test_call_content_yok(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(json.dumps({"id": "msg_1"}).encode("utf-8"))

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError, match="beklenmedik yanıt"):
        p("g", [])


# ---------- AC9: çok satırlı yanıt ----------

def test_call_cok_satirli_ilk_satir(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [
                        {
                            "type": "text",
                            "text": "write:out.txt:1\nİkinci satır — atılır\n",
                        }
                    ],
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    assert p("g", []) == "write:out.txt:1"


# ---------- AC10: UTF-8 ----------

def test_call_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [
                        {"type": "text", "text": "write:çıkış.txt:merhaba 🚀"}
                    ],
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    assert p("g", []) == "write:çıkış.txt:merhaba 🚀"


# ---------- AC11: context 006 injection ----------

def test_006_context_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, **_kw: Any) -> _FakeResponse:
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(
            json.dumps(
                {"content": [{"type": "text", "text": "write:x.txt:1"}]}
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    ctx = "## GBrain bağlamı\n- [[hello]] (skor 3.0): merhaba dünya"
    p = make_planner(_goal_llm(), context=ctx)
    p("g", [])
    content = seen["body"]["messages"][0]["content"]
    assert "Önceden bilinen bağlam (GBrain):" in content
    assert "[[hello]]" in content


# ---------- URL override ----------

def test_url_override(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_ANTHROPIC_URL", "https://vekil.local/v1/messages")
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, **_kw: Any) -> _FakeResponse:
        seen["url"] = req.full_url
        return _FakeResponse(
            json.dumps(
                {"content": [{"type": "text", "text": "write:x.txt:1"}]}
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    p("g", [])
    assert seen["url"] == "https://vekil.local/v1/messages"


# ---------- Model override ----------

def test_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_MODEL", "claude-3-opus-latest")
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, **_kw: Any) -> _FakeResponse:
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(
            json.dumps(
                {"content": [{"type": "text", "text": "write:x.txt:1"}]}
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    p("g", [])
    assert seen["body"]["model"] == "claude-3-opus-latest"


# ---------- Hata mesajı sırrı sızdırmaz ----------

def test_key_asla_hata_mesajina_gecmez(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_LLM", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-SUPER-SECRET-abcdef")

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise urllib_error.URLError("boom")

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError) as exc_info:
        p("g", [])
    assert "sk-SUPER-SECRET" not in str(exc_info.value)

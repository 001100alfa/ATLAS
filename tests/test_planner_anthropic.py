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


# ---------- SPEC 011: token cost trace ----------

def test_011_usage_trace_env_acikken(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC1+AC2: trace açık → stderr'a `[llm] anthropic tokens: ...` satırı."""
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_TRACE", "1")

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1"}],
                    "usage": {"input_tokens": 123, "output_tokens": 45},
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    p("g", [])
    err = capsys.readouterr().err
    assert "[llm] anthropic tokens:" in err
    assert "in=123" in err
    assert "out=45" in err
    # Fiyat env'i yok → cost=?
    assert "cost≈?" in err


def test_011_usage_trace_env_kapali(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC3: trace kapalı → stderr temiz."""
    _prep_key(monkeypatch)
    monkeypatch.delenv("ATLAS_LLM_TRACE", raising=False)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1"}],
                    "usage": {"input_tokens": 123, "output_tokens": 45},
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    p("g", [])
    assert "[llm]" not in capsys.readouterr().err


def test_011_cost_hesabi(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC4: fiyat env'i verilirse cost hesaplanır (per million USD)."""
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_TRACE", "1")
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "3.0")   # $3/M input
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15.0")  # $15/M output

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1"}],
                    "usage": {"input_tokens": 1000, "output_tokens": 200},
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    p("g", [])
    err = capsys.readouterr().err
    # 1000 * 3/1e6 + 200 * 15/1e6 = 0.003 + 0.003 = 0.006
    assert "cost≈$0.006000" in err


def test_011_usage_alani_yok(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """response'da usage yok → in=0 out=0 (fail-safe)."""
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_TRACE", "1")

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {"content": [{"type": "text", "text": "write:x.txt:1"}]}
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    p("g", [])
    err = capsys.readouterr().err
    assert "in=0 out=0" in err


def test_011_fiyat_env_bozuk(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Fiyat env parse hatası → cost≈? (fail-safe, çağrı kırılmaz)."""
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_TRACE", "1")
    monkeypatch.setenv("ATLAS_LLM_PRICE_IN", "not-a-number")
    monkeypatch.setenv("ATLAS_LLM_PRICE_OUT", "15.0")

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1"}],
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    assert p("g", []) == "write:x.txt:1"  # çağrı bozulmaz
    assert "cost≈?" in capsys.readouterr().err


# ---------- SPEC 014: Retry-After header ----------


def _http_error_with_headers(
    code: int, body: bytes, retry_after: str | None = None
) -> urllib_error.HTTPError:
    """`urllib_error.HTTPError` üretici — headers ile."""
    from email.message import Message
    hdrs: Message = Message()
    if retry_after is not None:
        hdrs["Retry-After"] = retry_after
    return urllib_error.HTTPError(
        url="https://api.anthropic.com/v1/messages",
        code=code,
        msg="throttled",
        hdrs=hdrs,  # type: ignore[arg-type]
        fp=io.BytesIO(body),
    )


def test_014_http_429_with_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    """429 + Retry-After → RetryAfterError (LLMPlannerError alt sınıfı)."""
    from atlas_core.orchestrator.planner import RetryAfterError
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise _http_error_with_headers(429, b"rate limit", retry_after="42")

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(RetryAfterError) as exc_info:
        p("g", [])
    assert exc_info.value.retry_after_s == 42.0
    assert "retry_after=42" in str(exc_info.value)


def test_014_http_429_without_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    """429 ama Retry-After yok → normal LLMPlannerError (RetryAfterError DEĞİL)."""
    from atlas_core.orchestrator.planner import RetryAfterError
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise _http_error_with_headers(429, b"rate limit", retry_after=None)

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError) as exc_info:
        p("g", [])
    assert not isinstance(exc_info.value, RetryAfterError)


def test_014_retry_after_parse_hata_normal_hata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retry-After başlığı parse edilemez → normal LLMPlannerError."""
    from atlas_core.orchestrator.planner import RetryAfterError
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise _http_error_with_headers(
            429, b"rate limit", retry_after="not-a-number"
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(LLMPlannerError) as exc_info:
        p("g", [])
    assert not isinstance(exc_info.value, RetryAfterError)


def test_014_http_529_with_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    """529 (Anthropic overload) + Retry-After → RetryAfterError."""
    from atlas_core.orchestrator.planner import RetryAfterError
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        raise _http_error_with_headers(529, b"overloaded", retry_after="10")

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())
    with pytest.raises(RetryAfterError) as exc_info:
        p("g", [])
    assert exc_info.value.retry_after_s == 10.0


# ---------- SPEC 013: on_usage callback → CallBudget.charge_tokens ----------

def test_013_on_usage_cagrilir(monkeypatch: pytest.MonkeyPatch) -> None:
    """M4: response usage varsa on_usage(in, out) çağrılır."""
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1"}],
                    "usage": {"input_tokens": 123, "output_tokens": 45},
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    captured: list[tuple[int, int]] = []
    p = make_planner(_goal_llm(), on_usage=lambda i, o: captured.append((i, o)))
    p("g", [])
    assert captured == [(123, 45)]


def test_013_on_usage_none_no_op(monkeypatch: pytest.MonkeyPatch) -> None:
    """on_usage=None (varsayılan) → callback çağrısı yok, planner çalışır."""
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1"}],
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    p = make_planner(_goal_llm())  # on_usage None
    assert p("g", []) == "write:x.txt:1"  # normal çalışır


def test_013_on_usage_butce_asim_planner_asagi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """on_usage bütçe aşımı fırlatırsa planner tam onu iletir
    (LLMPlannerError sarmalaması YOK)."""
    from atlas_core.orchestrator.core import BudgetExceededError
    _prep_key(monkeypatch)

    def fake_urlopen(*_a: Any, **_kw: Any) -> _FakeResponse:
        return _FakeResponse(
            json.dumps(
                {
                    "content": [{"type": "text", "text": "write:x.txt:1"}],
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                }
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)

    def raiser(_i: int, _o: int) -> None:
        raise BudgetExceededError("token aşımı")

    p = make_planner(_goal_llm(), on_usage=raiser)
    with pytest.raises(BudgetExceededError, match="token aşımı"):
        p("g", [])


# ---------- Hata mesajı sırrı sızdırmaz ----------

# ---------- SPEC 010: llm_prompt anthropic `system` alanına gider ----------

def test_010_llm_prompt_system_alaninda(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC1: goal.llm_prompt anthropic body.system alanına yazılır;
    messages[0].content'te YOKTUR."""
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
    from dataclasses import replace
    g = replace(_goal_llm(), llm_prompt="ROLE: mimarî danışman")
    p = make_planner(g)
    p("g", [])
    body = seen["body"]
    # system alanı llm_prompt'u taşır
    assert body["system"] == "ROLE: mimarî danışman"
    # messages[0].content'te llm_prompt YOK; ATLAS varsayılan gövdesi VAR
    content = body["messages"][0]["content"]
    assert "ROLE:" not in content
    assert "dosya yaz" in content  # görev metni
    assert "TEK SATIRLIK" in content
    # include_system=False → varsayılan "planlama alt-ajansısın" cümlesi VAR
    assert "planlama alt-ajansısın" in content


def test_010_llm_prompt_yok_system_alani_da_yok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC2: llm_prompt None → body'de system alanı eklenmez."""
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
    p = make_planner(_goal_llm())  # llm_prompt=None
    p("g", [])
    assert "system" not in seen["body"]


def test_010_llm_prompt_bos_system_alani_da_yok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC2b: llm_prompt boş string → system yok."""
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
    from dataclasses import replace
    # Goal dataclass frozen, replace ile llm_prompt="" verirsek
    # anthropic backend'de `system = goal.llm_prompt or None` boş string
    # falsy → None (alan gönderilmez).
    g = replace(_goal_llm(), llm_prompt="")
    p = make_planner(g)
    p("g", [])
    assert "system" not in seen["body"]


# ---------- SPEC 009: goal.llm_model önceliği ----------

def test_009_goal_llm_model_env_ustune(monkeypatch: pytest.MonkeyPatch) -> None:
    """goal.llm_model set edilirse env değil goal kullanılır."""
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_MODEL", "claude-3-haiku-latest")  # env AŞILACAK
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, **_kw: Any) -> _FakeResponse:
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(
            json.dumps(
                {"content": [{"type": "text", "text": "write:x.txt:1"}]}
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    from dataclasses import replace
    g = replace(_goal_llm(), llm_model="claude-3-opus-latest")
    p = make_planner(g)
    p("g", [])
    assert seen["body"]["model"] == "claude-3-opus-latest"  # env değil, goal


def test_009_goal_llm_model_yok_env_dusuyor(monkeypatch: pytest.MonkeyPatch) -> None:
    """goal.llm_model None → env yolu kullanılır (mevcut davranış)."""
    _prep_key(monkeypatch)
    monkeypatch.setenv("ATLAS_LLM_MODEL", "claude-3-haiku-latest")
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, **_kw: Any) -> _FakeResponse:
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(
            json.dumps(
                {"content": [{"type": "text", "text": "write:x.txt:1"}]}
            ).encode("utf-8")
        )

    monkeypatch.setattr(planner_mod.urllib_request, "urlopen", fake_urlopen)
    # goal.llm_model = None (varsayılan)
    p = make_planner(_goal_llm())
    p("g", [])
    assert seen["body"]["model"] == "claude-3-haiku-latest"


def test_009_goal_llm_model_ve_env_yok_varsayilan(monkeypatch: pytest.MonkeyPatch) -> None:
    """goal + env yok → _DEFAULT_ANTHROPIC_MODEL."""
    _prep_key(monkeypatch)
    monkeypatch.delenv("ATLAS_LLM_MODEL", raising=False)
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
    assert seen["body"]["model"] == planner_mod._DEFAULT_ANTHROPIC_MODEL


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

"""SPEC 059 — atlas metrics --alert-email SMTP alert."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas_core.cli import _send_alert_email, main


def _env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Metrics dosyası + minimum env."""
    metrics = tmp_path / "metrics.jsonl"
    monkeypatch.setenv("ATLAS_METRICS", str(metrics))
    monkeypatch.setenv("ATLAS_AUDIT", str(tmp_path / "a.jsonl"))
    monkeypatch.setenv("ATLAS_SANDBOX", str(tmp_path / "sb"))
    monkeypatch.setenv("ATLAS_VAULT", str(tmp_path / "v"))
    return metrics


def _write_metrics(path: Path, records: list[dict]) -> None:
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ═════════════════════════════════════════════════════════════════════
# _send_alert_email (birim, SMTP monkey)
# ═════════════════════════════════════════════════════════════════════


class _FakeSMTP:
    """smtplib.SMTP monkey — çağrıları yakalar, gönderim yapmaz."""

    def __init__(self, host: str, port: int, timeout: float = 10.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.starttls_called = False
        self.login_called: tuple[str, str] | None = None
        self.sent_messages: list = []

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def starttls(self):
        self.starttls_called = True

    def login(self, user, password):
        self.login_called = (user, password)

    def send_message(self, msg):
        self.sent_messages.append(msg)


def test_059_send_email_smtp_host_yok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ATLAS_SMTP_HOST tanımlı değil → False + hata mesajı."""
    monkeypatch.delenv("ATLAS_SMTP_HOST", raising=False)
    ok, err = _send_alert_email("s", "b")
    assert ok is False
    assert "ATLAS_SMTP_HOST" in err


def test_059_send_email_from_yok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")
    monkeypatch.delenv("ATLAS_ALERT_FROM", raising=False)
    monkeypatch.setenv("ATLAS_ALERT_TO", "a@x.com")
    ok, err = _send_alert_email("s", "b")
    assert ok is False
    assert "ATLAS_ALERT_FROM" in err


def test_059_send_email_to_yok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")
    monkeypatch.setenv("ATLAS_ALERT_FROM", "from@x.com")
    monkeypatch.delenv("ATLAS_ALERT_TO", raising=False)
    ok, err = _send_alert_email("s", "b")
    assert ok is False
    assert "ATLAS_ALERT_TO" in err


def test_059_send_email_port_int_degil(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")
    monkeypatch.setenv("ATLAS_SMTP_PORT", "not-int")
    monkeypatch.setenv("ATLAS_ALERT_FROM", "f@x.com")
    monkeypatch.setenv("ATLAS_ALERT_TO", "t@x.com")
    ok, err = _send_alert_email("s", "b")
    assert ok is False
    assert "PORT" in err


def test_059_send_email_basari_starttls_login_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env tam + fake SMTP → send_message çağrılır; starttls+login etkin."""
    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")
    monkeypatch.setenv("ATLAS_SMTP_PORT", "587")
    monkeypatch.setenv("ATLAS_SMTP_USER", "u")
    monkeypatch.setenv("ATLAS_SMTP_PASSWORD", "p")
    monkeypatch.setenv("ATLAS_SMTP_STARTTLS", "1")
    monkeypatch.setenv("ATLAS_ALERT_FROM", "from@x.com")
    monkeypatch.setenv("ATLAS_ALERT_TO", "a@x.com,b@x.com")

    fakes: list[_FakeSMTP] = []

    class _Capture(_FakeSMTP):
        def __init__(self, host, port, timeout=10.0):
            super().__init__(host, port, timeout)
            fakes.append(self)

    monkeypatch.setattr("smtplib.SMTP", _Capture)
    ok, err = _send_alert_email("konu", "gövde")
    assert ok is True
    assert err == ""
    assert len(fakes) == 1
    f = fakes[0]
    assert f.host == "smtp.local"
    assert f.port == 587
    assert f.starttls_called is True
    assert f.login_called == ("u", "p")
    assert len(f.sent_messages) == 1
    msg = f.sent_messages[0]
    assert msg["Subject"] == "konu"
    assert msg["From"] == "from@x.com"
    assert msg["To"] == "a@x.com, b@x.com"
    assert "gövde" in msg.get_content()


def test_059_send_email_starttls_kapali(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """STARTTLS='0' → starttls çağrılmaz."""
    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")
    monkeypatch.setenv("ATLAS_SMTP_STARTTLS", "0")
    monkeypatch.setenv("ATLAS_ALERT_FROM", "f@x.com")
    monkeypatch.setenv("ATLAS_ALERT_TO", "t@x.com")
    monkeypatch.delenv("ATLAS_SMTP_USER", raising=False)
    monkeypatch.delenv("ATLAS_SMTP_PASSWORD", raising=False)

    fakes: list[_FakeSMTP] = []

    class _Capture(_FakeSMTP):
        def __init__(self, host, port, timeout=10.0):
            super().__init__(host, port, timeout)
            fakes.append(self)

    monkeypatch.setattr("smtplib.SMTP", _Capture)
    ok, _ = _send_alert_email("s", "b")
    assert ok is True
    assert fakes[0].starttls_called is False
    assert fakes[0].login_called is None  # user/password yok


def test_059_send_email_smtp_exception_yakalanir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SMTP exception → False + hata mesajı; raise etmez."""

    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")
    monkeypatch.setenv("ATLAS_ALERT_FROM", "f@x.com")
    monkeypatch.setenv("ATLAS_ALERT_TO", "t@x.com")

    class _Broken:
        def __init__(self, *a, **kw):
            raise OSError("connection refused")

    monkeypatch.setattr("smtplib.SMTP", _Broken)
    ok, err = _send_alert_email("s", "b")
    assert ok is False
    assert "SMTP hatası" in err


# ═════════════════════════════════════════════════════════════════════
# CLI --alert-email
# ═════════════════════════════════════════════════════════════════════


def test_059_cli_alert_email_esik_asilinca_gonderilir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cache-hit %0 < eşik %50 + --alert-email → SMTP çağrılır + exit 8."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])

    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")
    monkeypatch.setenv("ATLAS_ALERT_FROM", "f@x.com")
    monkeypatch.setenv("ATLAS_ALERT_TO", "t@x.com")

    fakes: list[_FakeSMTP] = []

    class _Capture(_FakeSMTP):
        def __init__(self, host, port, timeout=10.0):
            super().__init__(host, port, timeout)
            fakes.append(self)

    monkeypatch.setattr("smtplib.SMTP", _Capture)
    rc = main(["metrics", "--alert", "50", "--alert-email"])
    assert rc == 8
    err = capsys.readouterr().err
    assert "UYARI: cache-hit" in err
    assert "[alert-email] gönderildi" in err
    assert len(fakes) == 1
    msg = fakes[0].sent_messages[0]
    assert "[ATLAS]" in msg["Subject"]
    assert "cache-hit" in msg["Subject"]


def test_059_cli_alert_email_env_eksik_uyari_ama_exit_8(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Env eksik → gönderim başarısız + stderr + exit 8 KORUR."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    monkeypatch.delenv("ATLAS_SMTP_HOST", raising=False)

    rc = main(["metrics", "--alert", "50", "--alert-email"])
    assert rc == 8  # exit 8 korunur, email gönderilmese bile
    err = capsys.readouterr().err
    assert "UYARI: cache-hit" in err
    assert "[alert-email] gönderim başarısız" in err
    assert "ATLAS_SMTP_HOST" in err


def test_059_cli_alert_email_esik_asilmadi_email_gonderilmez(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cache-hit yeterince yüksek → alert tetiklenmez → email de gönderilmez."""
    metrics = _env(monkeypatch, tmp_path)
    # in=100 + cache_r=900 → hit_ratio ~90%
    _write_metrics(metrics, [{
        "ts": "t", "in": 100, "out": 50, "cache_c": 0, "cache_r": 900,
    }])
    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")

    calls: list = []
    class _Capture(_FakeSMTP):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            calls.append(self)

    monkeypatch.setattr("smtplib.SMTP", _Capture)
    rc = main(["metrics", "--alert", "50", "--alert-email"])
    assert rc == 0  # eşik aşılmadı
    assert len(calls) == 0  # SMTP hiç çağrılmadı
    err = capsys.readouterr().err
    assert "UYARI" not in err
    assert "[alert-email]" not in err


def test_059_cli_alert_yok_email_bayragi_etkisiz(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--alert-email` VAR ama `--alert` yok → alert kontrolü çalışmaz."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.local")

    calls: list = []
    class _Capture(_FakeSMTP):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            calls.append(self)

    monkeypatch.setattr("smtplib.SMTP", _Capture)
    rc = main(["metrics", "--alert-email"])
    assert rc == 0
    assert len(calls) == 0
    err = capsys.readouterr().err
    assert "[alert-email]" not in err


def test_059_cli_alert_yok_email_yok_bit_uyumlu(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SPEC 029 mevcut davranış: --alert PCT + eşik aşıldı → stderr + exit 8."""
    metrics = _env(monkeypatch, tmp_path)
    _write_metrics(metrics, [{"ts": "t", "in": 100, "out": 50}])
    rc = main(["metrics", "--alert", "50"])
    assert rc == 8
    err = capsys.readouterr().err
    assert "UYARI: cache-hit" in err
    assert "[alert-email]" not in err  # bit-uyumluluk (yeni satır yok)

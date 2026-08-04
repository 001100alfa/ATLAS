# Görev 059 — Teslim

`atlas metrics --alert-email` — SMTP alert notify.

## Uygulama

- **`_send_alert_email(subject, body) -> (ok, err)`** (yeni):
  - stdlib `smtplib.SMTP` + `email.message.EmailMessage`.
  - Env kontrolü: HOST/PORT/USER/PASSWORD/STARTTLS + FROM/TO.
  - `smtp.starttls()` opsiyonel (STARTTLS env "1"/"true"/"yes").
  - `smtp.login(user, password)` opsiyonel (ikisi de varsa).
  - `smtp.send_message(msg)`.
  - Exception (`SMTPException/OSError/TimeoutError`) → yakalanır,
    `(False, "SMTP hatası: ...")`.
- **`_cmd_metrics`**: alert eşiği aşıldı bloğuna `if
  getattr(args, "alert_email", False):` dallanması. Email başarılı →
  stderr `[alert-email] gönderildi`; başarısız → `[alert-email]
  gönderim başarısız: <err>`. **Exit 8 KORUR** (alert semantiği email
  yan etkiden bağımsız).
- **Parser**: `--alert-email` (store_true) bayrak.

## Kanıtlar

- +12 test (`tests/test_cli_metrics_alert_email.py`):
  - **Birim `_send_alert_email` (7)**: HOST yok, FROM yok, TO yok,
    PORT int değil, başarı (starttls+login+send captured),
    STARTTLS='0' (starttls çağrılmaz + user/password yoksa login yok),
    SMTP exception yakalanır.
  - **CLI (5)**: eşik aşılınca gönderilir + exit 8,
    env eksik → gönderim başarısız + exit 8 KORUR,
    eşik aşılmadı → email gönderilmez, --alert yok → --alert-email
    etkisiz, SPEC 029 --alert PCT bit-uyumlu (alert-email yok).
- Mevcut 29+ metrics testi (SPEC 023 + 029 + 043 + 051) BİT-UYUMLU.
- 983 → **995 yeşil**, 12 skip, cov %91.43 → %91.53.
- `uv run mypy src` temiz (31 kaynak).
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- `atlas metrics --alert PCT --alert-email` bayrak kombinasyonu.
- Yeni env sözleşmesi: `ATLAS_SMTP_HOST/PORT/USER/PASSWORD/STARTTLS`
  + `ATLAS_ALERT_FROM/TO`.
- Yeni yardımcı `_send_alert_email`.

## Değişmeyen sözleşme

- `atlas metrics` mevcut çıktıları BİT-UYUMLU.
- `atlas metrics --alert PCT` (email yok) BİT-UYUMLU (SPEC 029).
- Exit kodu 8 (SPEC 029) — email yan etkiden bağımsız korunur.

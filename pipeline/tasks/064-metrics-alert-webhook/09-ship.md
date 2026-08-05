# Görev 064 — Teslim

`atlas metrics --alert-webhook URL` — POST JSON webhook (SMTP kardeşi).

## Uygulama

- `_post_alert_webhook(url, payload, timeout=5.0)`:
  - stdlib `urllib.request`; Content-Type + UA header.
  - HTTPError/URLError/OSError/TimeoutError yakalanır; non-2xx False + err.
  - Scheme http/https dışı → False + `"scheme geçersiz"` (SSRF savunma).
- `_cmd_metrics` alert dallanmasında: `--alert-webhook` verildiyse
  payload dict oluştur + POST + stderr'e sonucu bas. **Exit 8 KORUR**.
- Parser: `--alert-webhook URL` bayrak. `--alert-email` ile ortogonal.

## Kanıt

- +10 test (`tests/test_cli_metrics_alert_webhook.py`):
  - Birim (5): 200, payload+headers, 500, connect refused, scheme.
  - CLI (5): eşik aşıldı POST + exit 8, 500 exit 8 KORUR, eşik aşılmadı
    POST yok, email+webhook ortogonal, --alert yok webhook etkisiz.
- 1025 → **1035 yeşil**, 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 023/029/043/051/059 hepsi BİT-UYUMLU.
- Exit 8 semantiği KORUR (webhook yan etkiden bağımsız).

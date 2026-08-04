# Görev 051 — İhtiyaç

SPEC 043 (`metrics --format prometheus`) + SPEC 047 (`doctor --format
prometheus`) tek çağırışlık text export veriyor. Ama Prometheus'un
scrape modeli push değil pull: bir HTTP endpoint gerek. Şu an
`cronjob → text file → node_exporter textfile collector` işi görüyor
ama:
- Fresh veri için scrape interval'ından daha sık çalıştırma gerekir
- Textfile collector opsiyonel dependency
- Uzak makinede scrape edilemiyor (yalnız textfile hediyle)

## Kabul kriteri

- `atlas metrics --serve HOST:PORT` — blocking HTTP server; her scrape'te
  `.atlas/metrics.jsonl` tekrar okunur (canlı).
- `atlas doctor --serve HOST:PORT` — aynı, her scrape'te
  `_collect_doctor_report()` tekrar çalıştırılır.
- Endpoint: `GET /metrics` ve `GET /` — Prometheus text v0.0.4;
  diğer path'ler 404.
- Content-Type: `text/plain; version=0.0.4; charset=utf-8`.
- HOST:PORT formatı: `:PORT` (default host 127.0.0.1) veya
  `HOST:PORT`. Port 0 = OS ephemeral (test/dev).
- `--serve` mutex:
  - `metrics`: `--json`, `--format`, `--serve` aynı grup.
  - `doctor`: `--json`, `--schema`, `--format`, `--serve` aynı grup.
- Ek mutex (semantik): `doctor --ping --serve` → exit 2 (her istek
  anthropic quota tüketir; SPEC HATASI).
- `body_fn()` exception → 500 (server çökmez).
- Access log SESSİZ.
- Ctrl+C → nazikçe kapan.

## Riskli

- Server thread bind eder ama `serve_forever()` main thread'de
  çağrılır — `ready_cb` (test/monitör) AYRI thread'de çağrılmalı,
  aksi hâlde accept döngüsü başlamaz ve client timeout olur. (Kod
  içinde bu bug'ı düzelttim.)
- Latin-1 HTTP status message zorunluluğu — Türkçe 500 mesajı
  UnicodeEncodeError. Çözüm: status mesajı İngilizce (`Internal
  Server Error`), detay UTF-8 body'de.
- Stdlib `ThreadingHTTPServer` — eşzamanlı istekler kabul; heavy
  scrape scenarios için yeterli.

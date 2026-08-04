# Görev 055 — İhtiyaç

SPEC 028 `atlas replay --list --json` snapshot çıktı verir. Ama
dashboard/UI için canlı bir HTTP endpoint gerek — CLI çağrısı yerine.

SPEC 051 `--serve` kalıbı Prometheus text için tasarlandı; JSON için
`content_type` parametrize edilmeli (refactor).

## Kabul kriteri

- `atlas replay --serve HOST:PORT` yeni bayrak.
- `GET /` ve `GET /runs` → `_collect_replay_runs(limit)` JSON dizi
  (application/json; charset=utf-8).
- `--limit N` bayrağı SPEC 028'den; serve modunda her istek yeniden
  okur (canlı liste).
- Mutex:
  - `--serve + --list` → exit 2 (semantik)
  - `--serve + <run-id>` → exit 2 (server tüm liste yayımlar)
- SPEC 028 `--list --json` çıktı sözleşmesiyle BİT-UYUMLU: aynı
  `_collect_replay_runs` yardımcısı; JSON dizi (run_id/mtime/goal
  alanları).

## Yeniden kullanım (refactor)

- `observability/prometheus_server.py::make_handler` + `serve_prometheus_http`:
  - `content_type` parametrik (default Prometheus v0.0.4).
  - `allowed_paths` parametrik (default `("/", "/metrics")`).
  - Handler class adı `_AtlasHTTPHandler` (Prometheus özel değil artık).
- Mevcut metrics/doctor çağırıcıları default parametrelerle etkilenmez
  → SPEC 051 bit-uyumluluk.

## Riskli

- `_AtlasHTTPHandler` sınıf adı değişikliği: eski `_PrometheusHandler`
  private idi, dışardan import edilmiyor. Sınıf adı public API değil,
  yalnız kod içi.
- JSON payload büyük olabilir (100+ run). Limit default 20 yeterli.
- SPEC 051 test'lerinde class adı değişti → `_PrometheusHandler` →
  `_AtlasHTTPHandler`. Testler class adına bakmadığı için etki yok.

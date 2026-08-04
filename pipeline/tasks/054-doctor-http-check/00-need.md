# Görev 054 — İhtiyaç

ATLAS dış bir HTTP servisiyle (LLM proxy, dashboard, MLflow) entegre
çalıştığında, sağlık kontrolü yalnız kendi ortamı için — dış bağımlılık
sağlığı raporlanmıyor.

## Kabul kriteri

- `atlas doctor --http-check URL` yeni bayrak.
- URL'ye HTTP GET at (timeout 5s, stdlib urllib.request).
- Raporda `quality.http_check` alanı:
  - `url`: string
  - `status_code`: int | None (bağlantı hatası → None)
  - `latency_ms`: float | None (2 ondalık; başarı yolunda ölçülür,
    connect hatasında None)
  - `warning`: str | None
    - `None`: 2xx
    - `"HTTP <code>"`: non-2xx
    - `"bağlantı hatası: <exc>"`: DNS/timeout/socket
    - `"URL scheme geçersiz: '<scheme>'"`: http/https dışı
- Prometheus export (SPEC 047 + 054):
  - `atlas_doctor_http_check_up 0|1` (gauge): 1=2xx, 0=warning
  - `atlas_doctor_http_check_latency_ms <f>` (gauge, opsiyonel):
    yalnız latency ölçüldüyse
- `--strict + warning` → exit 9 (SPEC 032 kalıbı).
- `--http-check` yoksa `quality.http_check` alanı YOK — bit-uyumluluk.

## Riskli

- HTTPS URL'lerde certificate validation stdlib urllib default'una
  bırakıldı (sertifika hatası → connect hatası).
- Test için 127.0.0.1:1 (kernel için ayrılmış port) — reachable
  değil garantisi.
- Test için ephemeral HTTP server (`ThreadingHTTPServer(0)`) —
  SPEC 051'de kullanıldığı kalıp yeniden.

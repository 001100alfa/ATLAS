# Görev 054 — Teslim

`atlas doctor --http-check URL` — dış HTTP servisi sağlık kontrolü.

## Uygulama

- **`_check_http(url, timeout=5.0)`** (yeni):
  - stdlib `urllib.request.urlopen` GET
  - Return: `{url, status_code, latency_ms, warning}`
  - HTTPError → status yakalanır, warning=`"HTTP <code>"`
  - URLError/TimeoutError/OSError → status=None, warning=`"bağlantı hatası: ..."`
  - Scheme http/https değil → warning=`"URL scheme geçersiz: ..."`
- **`_collect_doctor_report(scan_src_path, http_check_url)`**:
  yeni opsiyonel `http_check_url` parametresi. Verilirse
  `quality.http_check` alanı EKLENİR; yoksa YER ALMAZ (bit-uyumluluk).
- **`_cmd_doctor`**: `getattr(args, "http_check", None)` +
  `_collect_doctor_report(..., http_check_url=...)`. `--serve` dalı
  da http_check_url'i yeniden geçer (her scrape'te GET).
- **`_doctor_report_to_prometheus`**:
  - `atlas_doctor_http_check_up 0|1` (koşullu, http_check alanı varsa)
  - `atlas_doctor_http_check_latency_ms <f>` (koşullu, latency None
    değilse)
- **Parser**: `--http-check URL` metavar.

## Kanıtlar

- +15 test (`tests/test_cli_doctor_http_check.py`):
  - **Birim `_check_http` (6)**: 200/404/500 status, connect refused,
    scheme invalid, url alanı korunur.
  - **Report entegrasyon (2)**: http_check yoksa alan yok / http_check
    verildiyse eklenir.
  - **CLI (3)**: --http-check --json ile status_code, 500 + --strict
    → exit 9, --http-check yoksa bit-uyumlu.
  - **Prometheus export (4)**: up=1 (2xx), up=0 (500), yoksa satır
    yok, latency None → latency satır yok.
- Mevcut 100+ doctor testi BİT-UYUMLU.
- 944 → **959 yeşil**, 12 skip, cov %91.19 → %91.25.
- `uv run mypy src` temiz (31 kaynak).
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- `atlas doctor --http-check URL` bayrağı.
- Yeni Prometheus metrikleri: `atlas_doctor_http_check_up`,
  `atlas_doctor_http_check_latency_ms`.
- Yeni quality alanı: `http_check`.

## Değişmeyen sözleşme

- `atlas doctor` mevcut çıktıları (bayraksız, `--json`, `--schema`,
  `--format`, `--strict`, `--scan-src`, `--ping`, `--pretty`,
  `--serve`, `--diff`) BİT-UYUMLU.
- Prometheus format (SPEC 043/047) BİT-UYUMLU — sadece 2 yeni koşullu
  metrik.
- Exit kodları: 0/9 sınıfı (yeni exit yok).

# Görev 043 — İhtiyaç

`atlas metrics` bugün insan çıktısı + `--json` (ham liste) veriyor. Ama
production observability için Prometheus scrape hedefi gerekli:
- Node exporter yerine ATLAS'ın kendi metric endpoint'i (bir kez
  komut çağrılır, stdout scrape edilir).
- İnsan çıktısı LLM cost dashboardu için parse edilemez; JSON tam
  ham log, aggregate metrik değil.

## Kabul kriteri

- `atlas metrics --format {human,prometheus}` (mutex `--json` ile).
- Prometheus text v0.0.4 format:
  - `# HELP <name> <text>` + `# TYPE <name> counter|gauge` + değer satırı.
  - Metrikler:
    - `atlas_metrics_records_total` (counter) — kayıt sayısı
    - `atlas_metrics_tokens_prompt_total` (counter) — input token top
    - `atlas_metrics_tokens_completion_total` (counter) — output top
    - `atlas_metrics_cache_creation_tokens_total` (counter)
    - `atlas_metrics_cache_read_tokens_total` (counter)
    - `atlas_metrics_cache_hit_ratio` (gauge, 0-1)
    - `atlas_metrics_cost_usd_total` (counter) — env fiyat yoksa 0.0
    - `atlas_metrics_inflight_max` (gauge) — yalnız `inflight` alanı varsa
    - `atlas_metrics_inflight_avg` (gauge) — yalnız `inflight` alanı varsa
- Argparse mutex: `--json` ve `--format prometheus` çakışır → exit 2.
- Default (`--format` yok, `--json` yok) = SPEC 023 insan çıktısı
  BİT-UYUMLU. `--format human` = default davranış.
- `--json` (mevcut) = ham liste BİT-UYUMLU.
- `--alert` bayrağı: prometheus/human/json ile ortogonal — alert eşiği
  aşılırsa yine exit 8 (mevcut davranış korunur; ancak SPEC 043 metnin
  içinde alert semantiği değişmedi).

## Riskli

- `cache_hit_ratio` gauge olarak 0-1 arasında (Prometheus konvansiyonu
  ratio = ondalık, % değil). İnsan çıktısındaki `%` gösterimden farklı
  ölçekli — dashboard tarafı buna göre `* 100` yapmalı. HELP metninde
  yazılı.
- `records_total` aslında counter değil "pencere içindeki gözlem sayısı"
  (limit=20 default). Adı `_total` ama semantiği yanıltıcı olabilir;
  HELP metninde "observed in window" açıklaması var.

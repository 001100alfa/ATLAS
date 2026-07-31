# Görev 047 — İhtiyaç

SPEC 043 (`atlas metrics --format prometheus`) LLM çağrı metriklerini
scrape edilebilir yaptı. Ama doctor sağlık kontrolleri hâlâ yalnız
insan çıktısı + `--json` — Prometheus/Grafana dashboard'una girmiyor.
Observability tarafında iki farklı scrape hedefi (metrics + doctor)
tek arayüzden okunmalı: metric = niceliksel, doctor = niteliksel gate.

## Kabul kriteri

- Yeni bayrak: `atlas doctor --format {human,prometheus}`
- `--json`, `--schema`, `--format` üçlüsü MUTEX
  (`add_mutually_exclusive_group`) — argparse SystemExit(2).
- `--strict` format bağımsız çalışır: quality warning varsa exit 9
  (Prometheus çıktı da basılır — alertmanager scrape için).
- Prometheus metrikleri:
  - `atlas_doctor_up 1` (gauge) — komut çalıştıysa 1 (canonical `up`)
  - `atlas_doctor_warnings_total <n>` (gauge) — `report["warnings"]` len
  - `atlas_doctor_quality_healthy{field=...} 0|1` — her quality alanı
    için (1 = warning yok). Sıralama deterministik (`sorted(keys)`).
  - `atlas_doctor_scan_src_hits_total <n>` (gauge, opsiyonel) — yalnız
    `scan_src` alanı raporda varsa
  - `atlas_doctor_scan_src_unique_files <n>` (gauge, opsiyonel)
- Her metrik HELP + TYPE + değer satırı taşır.
- Default davranış (bayraksız + `--format human` + `--json` mevcut
  hâli) BİT-UYUMLU.

## Riskli

- `--json` ve `--schema` mevcut testlerde ayrı bayraklar olarak
  kullanılıyor; mutex grup içine almak semantiği bozmaz (aynı anda
  ikisi verilmiyor mevcut testlerde). Ancak `--json --schema`
  kombinasyonunu deneyen test varsa kırılır — kontrol edildi, yok.
- Ping ve retry_pricing gibi zamanla değişen alanları Prometheus'a
  koymak yerine bekliyoruz (SPEC 047 kapsam dışı; observability
  disiplini "her alan = zamanla stable-scrape mi" sorusundan geçmeli).

# Görev 179 — İhtiyaç

SPEC 132 `metrics --alert-history-show` alert-history NDJSON log okur;
SPEC 143 `--format prometheus` counter ailesi; SPEC 144 `--out --gzip`;
SPEC 148 `--strict` exit 4; SPEC 139 `--json --out`. Ama **record
biçimi için ayrı JSON şeması yok** — kullanıcı ne alanlar döneceğini
koddan bulmak zorunda.

## Kabul

- `atlas metrics --alert-history-show --schema [--pretty]`.
- SPEC 040/136/146/149/153/154 kalıbı — kısa devre; log dosyası
  gerekmez; JSON şema tanımı basar.
- JSON:
  - `schema_version` = "1"
  - `record_fields` (SPEC 126 NDJSON record biçimi): 10 alan
    (`ts`, `alert`, `hit_ratio_pct`, `threshold_pct`, `records`,
     `tokens_in`, `tokens_out`, `cache_creation`, `cache_read`,
     `channels`) + SPEC 169 iki opsiyonel alan
    (`alert_window_minutes`, `alert_window_records`).
  - `summary_fields` (SPEC 132 --json summary satırı): `type`,
    `path`, `count`, `total`.
  - `exit_codes`: 0/2/4.
  - `formats`: human (default), json (NDJSON stream + summary),
    prometheus (3 counter aile).
  - `notes`: SPEC 126/132/139/143/144/148/179 referansları.
- MUTEX: `--schema` YALNIZ `--alert-history-show` ile birlikte
  (metrics --schema SPEC 153 zaten mevcut — kısa devre ilk).
- `--pretty` indent=2.
- Diğer --alert-history-show argümanları (--out/--format/--strict)
  --schema modunda YOK sayılır (kısa devre önce).
- `--schema` YOKSA SPEC 132/143/144/148 mevcut davranışlar BİT-UYUMLU.

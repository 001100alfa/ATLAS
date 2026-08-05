# Görev 096 — Teslim

`atlas metrics --group-by KEY --format prometheus --out PATH`.

## Uygulama

- `_cmd_metrics` başında: `--out` + (`--group-by` yok VEYA
  `--format != prometheus`) → SPEC HATASI exit 2.
- Group Prometheus dalında `--out PATH` → `parent.mkdir` + `write_text`
  (SPEC 092 kalıbı ile simetrik).
- Yazma başarısız → SPEC HATASI exit 2.
- Dosya içeriği stdout modu ile BİT-UYUMLU.
- Parser: `--out PATH` metavar, default None.

## Kanıt

- +9 test (`tests/test_cli_metrics_group_prom_out.py`):
  - Dosya yazıldı, stdout Prometheus text basmaz.
  - Dosya içeriği stdout modu ile AYNI.
  - Parent auto-mkdir.
  - Yazma hatası (dosya=dizin) → exit 2.
  - MUTEX: group-by yok, format yok, tek başına (3 test).
  - --with-cost + --out → cost_usd metric dosyada.
  - --out YOKSA SPEC 090 stdout AYNI.
- 1335 → **1344 yeşil** (+9), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 090: `--out` yoksa stdout Prometheus grup çıktısı AYNI.
- SPEC 043/084 tekil ve --with-cost davranışları AYNI.

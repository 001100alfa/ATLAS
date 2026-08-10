# Görev 153 — İhtiyaç

SPEC 040/136/146/149 kalıbı metrics komutu için: `atlas metrics --schema`
kısa devre JSON şema tanımı basar (metrics.jsonl record alanları +
exit kodları + format seçenekleri).

## Kabul

- `atlas metrics --schema [--pretty]`.
- Metrics dosyası gerekmez — kısa devre (SPEC 040 kalıbı).
- JSON: `{schema_version, top_level, exit_codes, formats, notes}`.
- top_level 7 alan (SPEC 023 `_write_metric_for_data` şeması AYNI):
  ts, in, out, cache_c, cache_r, cost, inflight (SPEC 039 opsiyonel).
- exit_codes 0/2/8 (SPEC 023/029 kalıp).
- formats human/json/prometheus.
- `--pretty` indent=2.
- `--schema` YOKSA SPEC 023/029/043/076/081/084 metrics normal
  davranışlar BİT-UYUMLU.

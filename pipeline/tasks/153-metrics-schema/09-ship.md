# Görev 153 — Teslim

`atlas metrics --schema [--pretty]`.

## Uygulama
- `_cmd_metrics` başında `--schema` kısa devre (SPEC 040/136/146/149 kalıbı).
- metrics.jsonl gerekmez; JSON şema tanımı basılır.
- 7 top_level alan (SPEC 023 `_write_metric_for_data` şeması AYNI):
  - ts (ISO 8601), in, out, cache_c, cache_r, cost, inflight (SPEC 039).
- exit_codes 0/2/4/8 (SPEC 023/029/148 kalıp).
- formats human/json/prometheus (SPEC 023/043).
- notes: SPEC 023/029/043/051/059/064/068/076/081/084/096/103/126/132/143/144/148/153.
- Parser: `--schema` + `--pretty` eklendi.

## Kanıt
- +7 test (`tests/test_cli_metrics_schema.py`):
  - schema kısa devre + version="1"
  - 7 top_level alan (isim + sıra)
  - 4 exit_code (0/2/4/8)
  - 3 format (human/json/prometheus)
  - notes SPEC referansları (023/029/043/153)
  - --pretty indent=2
  - --schema YOKSA SPEC 023 normal davranış AYNI (bit-uyumlu)
- metrics regresyon 195 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 023 normal metrics özet AYNI (`--schema` yoksa).
- SPEC 029/043/076/081/084 vb. mevcut argümanlar DOKUNULMADI.
- SPEC 132/143/144/148 alert-history alt-ailesi DOKUNULMADI.

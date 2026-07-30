# Görev 039 — Teslim

`planner.py` — LLM inflight sayacı + metrics `inflight` alanı.

## Uygulama
- `_INFLIGHT_COUNT: int = 0` (module global) + `_INFLIGHT_LOCK = threading.Lock()`
- `_inflight_begin()`: `++COUNT`, yeni değeri döner (çağrıyı dahil sayarak)
- `_inflight_end()`: `max(0, COUNT-1)` (negatife düşmez, defensive)
- `_inflight_snapshot()`: anlık değer (test/introspection için)
- `_write_metric_for_data(data, inflight: int | None = None)`: kayda
  `inflight` alanı EKLENİR (yalnız verildiyse); None → mevcut şema
  (bit-uyumlu)
- `_call_anthropic`: **wrapper** — `_inflight_begin()` + `try/finally`
  + `_inflight_end()`; iş `_call_anthropic_inner` içinde. Wrapper hem
  başarı hem raise durumunda sayacı sıfırlar.

## Kanıtlar
- begin → 1 → 2; end → 1 → 0; end 0'da → 0 kalır
- 10 thread × 100 begin/end → sayaç 0 (thread-safe)
- metrics JSONL kaydında `inflight: 2` alanı
- `inflight=None` → alan YOK (bit-uyumluluk)
- `_call_anthropic_inner` raise → wrapper `finally` → sayaç 0
- Başarılı çağrı → sayaç 0
- +7 test (729 yeşil, cov %90.54)

## Değişmeyen sözleşme
- `_call_anthropic` public imzası aynı.
- Mevcut `_write_metric_for_data(data)` çağrıları bit-uyumlu (inflight
  default None).
- `.atlas/metrics.jsonl` şeması geniişledi — okuma tarafı yeni alanı
  görmezden gelmeli.

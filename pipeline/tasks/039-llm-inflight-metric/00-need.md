# Görev 039 — İhtiyaç

SPEC 031 ile paralel batch geldi (`--jobs N`) — aynı anda birden çok
LLM çağrısı yapılabiliyor. Ama `.atlas/metrics.jsonl` bir çağrının
inflight sırasında **kaç eş-zamanlı çağrı** olduğunu kaydetmiyor.
Rate limit debug'ı, API concurrent quota tuning'i için önemli.

## Kabul kriteri
- Global `_INFLIGHT_COUNT` + `threading.Lock` → begin/end/snapshot API.
- `_call_anthropic` her çağrı başında `_inflight_begin()` snapshot alır,
  wrapper `finally` ile `_inflight_end()` (leak yok).
- `_write_metric_for_data(data, inflight=<int>)` → metrics kaydına
  `inflight: int` alanı EKLENİR.
- `inflight=None` (default) → alan yazılmaz (mevcut SPEC 023 testleri
  BİT-UYUMLU geçer).
- Snapshot çağrıyı DAHİL sayar (1 çağrı varsa 1; 2 varsa 2).

## Riskli
- `_call_anthropic` fonksiyonu uzun — wrapper/inner ayrımı ile
  minimal invaziv try/finally.
- Snapshot noktası: çağrı başlangıcı — çağrı ortasında başka bir
  çağrı bitse bile snapshot değişmez (istatistik "başlangıçtaki
  concurrent count").
- Thread lock kısa; performans etkisi ihmal edilebilir (mikro-saniye).

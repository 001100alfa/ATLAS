# 023 — İhtiyaç: cache-hit metrikleri (`.atlas/metrics.jsonl`)

## Bağlam
SPEC 011 usage'ı stderr'a; SPEC 013 bütçeye; SPEC 015.1 cache
alanlarına yaydı. Ama çok-turlu bir görev süresinde **kaç
çağrının cache-hit aldığı** görünmüyor — sadece anlık trace var.
Kullanıcı "cache_control koydum, %90 tasarruf oluyor mu?" sorusunu
manuel olarak analiz etmek zorunda.

## İhtiyaç (tek cümle)
Her başarılı anthropic çağrısı sonrası `.atlas/metrics.jsonl`'a
tek satır JSON yazılsın: `{ts, in, out, cache_c, cache_r, cost}`;
yeni `atlas metrics` alt-komutu son N kaydı özetlesin (toplam
tokens, toplam cost, cache-hit oranı %).

## Ölçülebilir Başarı
- **M1 — Dosya yolu:** `_metrics_path()` — `ATLAS_METRICS`
  env veya varsayılan `.atlas/metrics.jsonl`. Klasör yoksa oluştur.
- **M2 — Kayıt:** `_write_metric(record)` yardımcısı — dict'i JSON
  serialize edip newline ile append eder. Idempotent değil (her
  çağrı bir satır).
- **M3 — Anthropic entegrasyon:** `_call_anthropic` başarılı
  yolun sonunda `_write_metric({"ts": ISO, "in": N, "out": N,
  "cache_c": N, "cache_r": N, "cost": "$X.XXXXXX"})`. Fiyat env
  yoksa cost=`"?"`.
- **M4 — CLI komutu:** `atlas metrics [--limit N] [--json]`.
  Varsayılan N=20; JSON istenirse tek satır liste `[{...}, ...]`.
- **M5 — İnsan format:**
  ```
  === ATLAS metrics — son 20 çağrı ===
    toplam: 20 çağrı
    input tokens:   1234
    output tokens:  567
    cache creation: 100
    cache read:     500
    cache-hit oranı: 40% (500 / 1234)
    tahmini cost:   $0.006543
  ```
- **M6 — Test:** +5 test — dosya yoksa yaz, append çalışır,
  `atlas metrics` insan format, `--json`, cache-hit oranı hesabı.
- **M7 — DECISIONS:** [KARAR] JSONL neden; entegrasyon noktası
  neden `_call_anthropic`.

## Kapsam DIŞI
- claude/acp usage — protokolde native değil.
- Metrikleri temizleme (`atlas metrics --clear`) — kullanıcı el
  ile `rm` yapar; YAGNI.
- Prometheus/OpenTelemetry export — YAGNI.
- Grafiksel dashboard — 024'te ayrı.

## Kısıt
- `_call_anthropic` yeni yan-etki (dosya yaz) — hata sessiz
  (metrics dosyası yazılamıyor diye plan başarılı olmasın).
- JSONL format: her satır bağımsız JSON; parse hatası satır atla.
- Türkçe komut çıktısı.

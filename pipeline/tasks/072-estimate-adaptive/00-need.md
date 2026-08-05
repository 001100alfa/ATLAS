# Görev 072 — İhtiyaç

SPEC 069 `--estimate` heuristik `tokens_per_call=500` — gerçek çağrı
maliyetinden uzak olabilir. Kullanıcının kendi metrics.jsonl'ında zaten
gerçek call token'ları var → ortalama daha isabetli tahmin verir.

## Kabul

- `atlas run --estimate --adaptive [--adaptive-n N]`:
  - `.atlas/metrics.jsonl` son N kaydı (default 20) `in+out+cache_c+
    cache_r` toplamı ortalaması.
  - < 3 kayıt veya dosya yok → static fallback + UYARI (source
    `adaptive-fallback-static`).
  - Yeterli numune → source `adaptive-avg` + `sample_count`.
- `--estimate` (adaptive YOK) → SPEC 069 static bit-uyumlu (source
  `static`).
- Rapor JSON'da `source` + `sample_count` alanları eklendi (JSON
  şema genişleme — bit-uyumluluk).

## Risk

- Static → adaptive geçiş: JSON şema alan eklendi (`source`,
  `sample_count`) — dış tüketici bit-uyumlu (var olan alanlar aynı).

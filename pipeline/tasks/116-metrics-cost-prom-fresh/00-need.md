# Görev 116 — İhtiyaç

SPEC 084 `--with-cost` + SPEC 090 `--format prometheus` + SPEC 103
`--out --gzip` bileşimi mevcut ama test'ler ayrı ayrı doğruluyor.
Tam zincirin **birlikte** çalıştığını (regresyon önleme için) tek
test dosyasında doğrula. Salt-testler + docs; kod değişikliği yok.

## Kabul

- Yeni `tests/test_cli_metrics_full_chain.py`.
- Test set: --group-by day + --with-cost + --format prometheus + --out
  + --gzip birlikte → dosya var + gzip + cost_usd metric + 6 metric
  ailesi.
- Kod DEĞİŞMEZ (sadece test artışı; regresyon net kanıt).

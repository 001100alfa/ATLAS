# Görev 122 — İhtiyaç

SPEC 090 `metrics --group-by --format prometheus` + `--limit N` birlikte
kullanıldığında sadece son N kaydın gruplandığı doğrulanmadı (regresyon
riski). Salt-test tur.

## Kabul

- Yeni `tests/test_cli_metrics_prom_limit.py`.
- Kod DEĞİŞMEZ; sadece `--limit N` slice'ının grup Prometheus'a önce
  uygulandığını + toplam sonuç değerlerinin doğru olduğunu doğrula.

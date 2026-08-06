# Görev 116 — Teslim

`tests/test_cli_metrics_full_chain.py` — SPEC 084+090+096+103 tam
zincir regresyon önleme.

## Uygulama
- Kod DEĞİŞMEZ (sadece 4 yeni test).
- Test: group-by day + with-cost + prometheus + out + gzip birlikte;
  dosya + magic gzip + 6 metric ailesi + cost 10.5 USD.
- Multi-day deterministik key sırası.
- --gzip olmadan düz metin.
- Env fiyat yok → cost 0.0 (fail-safe).

## Kanıt
- +4 test; 1457 → **1461 yeşil**, mypy/ruff temiz.

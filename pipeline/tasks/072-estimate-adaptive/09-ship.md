# Görev 072 — Teslim

`atlas run --estimate --adaptive` — metrics ortalaması ile isabetli tahmin.

## Uygulama

- `_read_metrics_avg_tokens(limit=20) -> (avg | None, sample_count)`:
  metrics.jsonl son N kaydı `in+out+cache_c+cache_r` ortalaması. < 3
  kayıt → None.
- `_estimate_run_cost(...)` `source` + `sample_count` alanları eklendi
  (JSON şema genişleme).
- `_cmd_run_goal` `--estimate` bloğu: `--adaptive` verildiyse
  `_read_metrics_avg_tokens(adaptive_n)`. Yeterli numune → source
  `adaptive-avg`. Yetersiz → static fallback + source `adaptive-fallback-
  static` + insan çıktısında UYARI.
- Parser: `--adaptive` + `--adaptive-n N` (default 20).
- Batch dispatcher: adaptive parametreleri iletilir.

## Kanıt

- +10 test (`tests/test_cli_run_estimate_adaptive.py`):
  - Birim (4): metrics yok → None, < 3 kayıt → None, 3+ ortalama
    hesap doğru (1000/3 = 333), limit uygulanır (son N).
  - CLI (6): --adaptive metrics kullanır (source=adaptive-avg + n),
    az kayıt fallback (source=adaptive-fallback-static), metrics yok
    fallback, --adaptive-n özel değer, insan çıktısında source görünür,
    --estimate (adaptive YOK) static bit-uyumlu.
- 1144 → **1154 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 069 `--estimate` (adaptive YOK) BİT-UYUMLU (source alanı yeni,
  tokens_per_call default 500 aynı).
- SPEC 023 metrics.jsonl salt-okunur (yazılmıyor).

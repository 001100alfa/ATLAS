# Görev 084 — İhtiyaç

SPEC 081 `--group-by hour|day` grup başına token toplamı verir. Fatura
takibi için grup başına $ cost da gerek; şu an kullanıcı manual
`ATLAS_LLM_PRICE_IN * tokens_in / 1M + ...` hesaplıyor. SPEC 043
Prometheus'ta cost var; group aggregation'da yok.

## Kabul

- `atlas metrics --group-by KEY --with-cost [--json]`.
- `--with-cost` **yalnız** `--group-by` ile birlikte anlamlı → sadece
  `--with-cost` (group-by yok) → SPEC HATASI exit 2.
- Cost formülü SPEC 043 Prometheus ile AYNI:
  `cost = in*price_in/1M + cache_c*price_in*1.25/1M
        + cache_r*price_in*0.1/1M + out*price_out/1M`.
- Env fiyat: `ATLAS_LLM_PRICE_IN`, `ATLAS_LLM_PRICE_OUT` (SPEC 013).
  Env yoksa/0 → cost 0.0 (fail-safe); pretty'de UYARI stderr.
- JSON şeması: grup dict'e `cost_usd: float` alanı EKLENİR (BİT-UYUMLU
  → mevcut alanlar korunur).
- Pretty tablo: yeni sütun `cost` (6 basamak $).
- `--with-cost` VERİLMEZSE davranış SPEC 081 BİT-UYUMLU (grup dict'te
  cost alanı YOK).

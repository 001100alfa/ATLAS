# Görev 069 — İhtiyaç

Kullanıcı `atlas run --goal-file X.yaml` çalıştırmadan önce şu bilgileri
görmek istiyor:
- Backend nedir (ATLAS_LLM=stub/anthropic/acp/claude)?
- Kaç LLM çağrısı planlanacak (max_steps üst sınır)?
- Tahmini token toplamı + $ cost?
- Fiyat env eksik mi?

SPEC 020 `--dry-run` mevcut ama planner'ı YİNE ÇALIŞTIRIYOR (LLM
çağırıyor); sadece action'ı stub yapıyor. Bu bir LLM çağrısı yapıyor
demek — cost öngörüsü DEĞİL.

## Kabul

- `atlas run --goal-file X --estimate` — LLM çağırmaz.
- Goal YAML yüklenir (SPEC hatası kontrolü); geçersiz → exit 2.
- Context enjeksiyon YAPILMAZ (GBrain hiç instantiate edilmez).
- Sandbox kurulmaz, planner fabrikası çağrılmaz, run_loop yok.
- Audit dosyasına `atlas-run` kaydı DÜŞMEZ.
- `_estimate_run_cost` hesabı:
  - `tokens_per_call` env `ATLAS_ESTIMATE_TOKENS_PER_CALL` (default 500;
    geçersiz int → fallback 500).
  - `total_tokens = max_steps * tokens_per_call`.
  - Backend `stub` VEYA fiyat env yok → cost 0.
  - Aksi: yarısı input yarısı output; cost = `(in*p_in + out*p_out)/1M`.
- Çıktı: default insan (backend/max_steps/budget/tokens/cost/fiyat env
  uyarısı); `--json` bit-hassas JSON.
- Exit 0 her koşulda (bilgi komutu).

## Risk

- Heuristik tokens_per_call — gerçek çağrı token'ları görev karmaşıklığına
  göre çok değişir. Kullanıcı env ile override edebilir. Gerçek metriklere
  dayalı adaptif hesap (SPEC 023 son N call ortalaması) YAGNI — gelecek
  SPEC 072?

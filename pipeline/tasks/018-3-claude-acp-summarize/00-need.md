# 018.3 — İhtiyaç: Claude + ACP real gözlem özetleme

## Bağlam
018.2 hook mekanizmasını (`_maybe_summarize_or_trim` + Goal alanı +
env) tam kurdu. Ama backend `claude` veya `acp` iken **stub'a
düşüyor** ve bir kez stderr uyarı basıyor ("018.3 kapsamı"). Bugün
018.3'ü kapatıp iki backend'de de real özet çağrısına bağlıyoruz.

## İhtiyaç (tek cümle)
`obs_summarize` opt-in aktifken ve backend `claude`/`acp` iken,
gözlem özetleme mevcut backend'in kendi çağrı fonksiyonunu (`_call_
claude` / `_call_acp`) minimal özet prompt'u ile tekrar kullanarak
gerçekleştirilsin.

## Ölçülebilir Başarı
- **M1 — Claude özet:** `_summarize_via_claude(obs, goal)` mevcut
  `_call_claude` çağırır — prompt: `"Aşağıdaki komut çıktısını
  Türkçe TEK cümlede, en fazla 120 karakterde özetle..."`. Response
  ilk satır alınır, 120 char'da kırpılır, `f"[özet: {line}]"` döner.
- **M2 — ACP özet:** `_summarize_via_acp(obs, goal)` aynı prompt ile
  `_call_acp` çağırır; response aynı biçimde döner.
- **M3 — Dispatch güncellemesi:** `_maybe_summarize_or_trim`:
  - `backend == "claude"` → `_summarize_via_claude`
  - `backend == "acp"` → `_summarize_via_acp`
  - `backend == "anthropic"` → `_summarize_via_anthropic` (018.2)
  - `backend == "stub"` → `_stub_summarize_obs` (018.2)
- **M4 — Fail-safe:** her real çağrı `LLMPlannerError` fırlatırsa →
  stderr uyarı + `_trim_obs` fallback (018.2 anthropic ile simetri).
- **M5 — Uyarı YOK:** claude/acp için "018.3 kapsamı" uyarısı artık
  BASILMAZ (mekanizma tam çalışıyor). Test uyarı setinin claude/acp
  için boş kaldığını doğrular.
- **M6 — Bit-uyumluluk:** `_call_claude`, `_call_acp`, `_resolve_
  claude_bin`, `_resolve_acp_bin` imzaları KORUNUR. Yalnız yeni
  yardımcı fonksiyonlar eklenir.
- **M7 — Test:** +5-6 test — claude mock ile real özet, acp mock
  ile real özet, claude LLMPlannerError fallback, acp
  LLMPlannerError fallback, kısa obs no-op (claude/acp de), uyarı
  YOK doğrulama.
- **M8 — DECISIONS:** [KARAR] her backend'in kendi çağrı fonksiyonu
  yeniden kullanıldı (ayrı özet kanalı YAGNI); ACP'de her özet için
  yeni oturum (session sızıntısı yok, mevcut kalıp).

## Kapsam DIŞI
- Özet önbelleği — YAGNI (obs history'de aynı adımdan gelmez).
- Structured özet (JSON) — düz metin yeter.
- Cost bütçesi ayrı env (`ATLAS_LLM_OBS_SUMMARIZE_BUDGET`) — YAGNI,
  mevcut CallBudget zaten sayar.
- Model override özet için ayrı env — YAGNI, planner ile aynı model.

## Kısıt
- `_trim_obs`, `_stub_summarize_obs`, `_summarize_via_anthropic`,
  `_maybe_summarize_or_trim`, `_call_claude`, `_call_acp` imzaları
  korunur.
- Türkçe uyarı + prompt (018.2 ile simetri).
- Test yalnız mock — network YOK.
- Windows cp1254 uyumu — üstsimge yok.

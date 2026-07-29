# 018.2 — İhtiyaç: LLM ile gerçek gözlem özetleme

## Bağlam
018 gözlemi baştan `obs_chars` char'a kırpıyor; 018.1 head+skip+tail
ile hatanın sonunu koruyor. Yine de uzun ve karmaşık gözlemlerde
(build log, stack trace) LLM planner "ne oldu bunu" görmüyor —
kırpılan orta blok anlamı taşıyor olabilir. LLM'in kendisine
"özetle" demek daha akıllı — ama ekstra çağrı = ekstra maliyet.

## İhtiyaç (tek cümle)
`Goal.obs_summarize: True` (veya `ATLAS_LLM_OBS_SUMMARIZE=1`) iken,
uzun gözlemler (`len > obs_chars`) LLM'e "tek satırda özetle"
istekliği ile gönderilsin; sonuç plan promptuna gömülsün.

## Ölçülebilir Başarı
- **M1 — Goal alanı:** `Goal.obs_summarize: bool = False` (opt-in).
  Eski YAML'lar (alan yok) `False` alır — bit-uyumlu.
- **M2 — Env override:** `ATLAS_LLM_OBS_SUMMARIZE=1` global override.
  Değer `1`, `true`, `yes` → aktif; başkası → yoksay.
- **M3 — Hook mekanizması:** `_summarize_or_trim(obs, obs_chars, goal,
  backend)` — effective aktif VE `len > obs_chars` ise summarizer,
  aksi `_trim_obs` (018.1 davranışı).
- **M4 — Stub summarizer (deterministik):** `ATLAS_LLM=stub` (veya
  test kolu) → `f"[özet: {N} char, {L} satır, baş: '<40 char>'...]"`
  formatı. Aynı input → aynı output.
- **M5 — Real summarizer (Anthropic):** `ATLAS_LLM=anthropic` + opt-in
  → `_summarize_via_anthropic(obs)` mevcut `_call_anthropic`'i yeni
  bir prompt ile çağırır: `"Bu gözlemi 1 cümlede, en fazla 120
  karakterde özetle:\n<obs[:2000]>"`. Response tek satır kesilir,
  120 char'da kırpılır.
- **M6 — Claude/ACP fallback:** bu backend'lerde real özet
  desteklenmiyor (018.3 kapsamı) → stub summarizer'a düşer + stderr
  bir kez uyarı basılır ("uyarı: obs_summarize claude/acp'de
  gerçek çağrı YAPMAZ — stub özet döner").
- **M7 — Cost etkisi:** anthropic real çağrı → ekstra token → mevcut
  metrics.jsonl'a yeni satır olarak yazılır (planner mevcut mekanizma).
  Test için `_write_metric_for_data` çağrı sayısı ölçülür.
- **M8 — Fail-safe:** özet LLM çağrısı `LLMPlannerError` fırlatırsa
  `_trim_obs`'a düş, hata stderr'e bas. Planner turu bloklamaz.
- **M9 — Kısa gözlem:** `len(obs) <= obs_chars` → summarizer
  ÇAĞRILMAZ (hem stub hem real). Ekstra maliyet yok.
- **M10 — Test:** +8 test (opt-in çalışır, kapalı=018.1 davranışı,
  env override, stub deterministik, kısa gözlem no-op, YAML yükleme,
  claude/acp uyarısı, fail-safe).
- **M11 — DECISIONS:** [KARAR] real çağrı yalnız anthropic; claude/acp
  neden 018.3'e ertelendi; env değer kabul kuralı.

## Kapsam DIŞI
- Claude subprocess veya ACP kanalı üzerinden real özet — 018.3
  (backend-agnostik özet kanalı ayrı iştir).
- Cost/token bütçe ayrı (`ATLAS_LLM_OBS_SUMMARIZE_BUDGET`) — YAGNI;
  mevcut cost sayacı zaten kaydeder.
- Özet önbelleği (aynı obs iki kez → tek çağrı) — YAGNI, obs zaten
  history içinde farklı adımdan gelir.
- Structured özet (JSON) — düz metin yeter.

## Kısıt
- `_trim_obs` sözleşmesi korunur — 018.1 varsayılan davranış.
- `Planner`, `make_planner`, `LLMPlannerError`, `RetryAfterError`
  imzaları korunur.
- Yeni env değişkeni: `ATLAS_LLM_OBS_SUMMARIZE` (0/1 varsayılan 0).
- Türkçe uyarı + prompt.
- Windows cp1254 uyumu — üstsimge yok.

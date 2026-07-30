# 018.3 — Ship

## Sonuç
- **Real özet 4 backend'de de aktif:**
  - `anthropic` → `_summarize_via_anthropic` (018.2, refactor)
  - `claude` → `_summarize_via_claude` (**YENİ**) — `_call_claude`
    subprocess minimal özet promptu ile.
  - `acp` → `_summarize_via_acp` (**YENİ**) — `_call_acp`
    JSON-RPC oturumu minimal özet promptu ile.
  - `stub` → `_stub_summarize_obs` (deterministik, LLM çağrısı yok).
- **Dispatch tablosu:** `_maybe_summarize_or_trim` içinde
  `{"anthropic":..., "claude":..., "acp":...}` sözlüğü — üç real
  backend simetrik. `.get(backend)` ile yumuşak fallback (bilinmeyen
  → stub).
- **Ortak yardımcılar:**
  - `_build_summarize_prompt(obs)` — Türkçe TEK cümle + 120 char +
    hataya odaklan promptu (3 backend paylaşır).
  - `_finalize_summary_line(text, backend_label)` — ilk satır +
    120 char kırpma + `[özet: ...]` biçimleme + boş cevap hatası.
- **Fail-safe:** herhangi bir real çağrı `LLMPlannerError` fırlatırsa
  → stderr `"uyarı: obs_summarize <backend> çağrısı başarısız
  (kırpmaya düşülüyor): <hata>"` + `_trim_obs` fallback. Planner
  turu ÖLMEZ.
- **018.2 "018.3 kapsamı" uyarısı kaldırıldı** — artık claude/acp
  real çağrı yapıyor, uyarı sadece hata durumunda çıkar.
- **Kısa obs bit-uyumlu:** `len(obs) <= obs_chars` → hiçbir backend
  çağrısı YAPILMAZ (ekstra maliyet yok). Test her backend için
  ayrı doğrular.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +_build_summarize_prompt,
                                            +_finalize_summary_line,
                                            +_summarize_via_claude,
                                            +_summarize_via_acp;
                                            _summarize_via_anthropic
                                              refactor (yardımcılara);
                                            _maybe_summarize_or_trim
                                              dispatch tablosu; 018.3
                                              uyarı yolu kaldırıldı)
tests/test_planner_obs_summarize.py       (edit: 2 eski uyarı testi
                                            silindi; +8 test 018.3
                                            bölümünde: claude/acp real
                                            çağrı, hata fallback,
                                            kısa obs no-op x2, uzun
                                            özet kırpma, bilinmeyen
                                            backend stub fallback)
pipeline/tasks/018-3-claude-acp-summarize/*.md  (2 artefakt)
```

## Sözleşme değişmezliği
- `_call_claude`, `_call_acp`, `_call_anthropic`, `_resolve_claude_bin`,
  `_resolve_acp_bin`, `_resolve_anthropic_env`, `_trim_obs`,
  `_stub_summarize_obs`, `_summarize_via_anthropic`,
  `_maybe_summarize_or_trim` imzaları KORUNDU.
- `Planner`, `make_planner`, `LLMPlannerError`, `RetryAfterError`
  imzaları korundu.
- `Goal.obs_summarize` alanı 018.2'den beri aynı.
- Yeni env DEĞİL, yeni Goal alanı DEĞİL — yalnız dispatch tamamlaması.

## Kalite kapıları
- pytest: **606 passed + 8 skipped** (600 → +6 net: +8 018.3 −2 eski)
- coverage: %91.23 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/018.3-claude-acp-summarize` — main üstünde tek commit.

## Env sözleşmesi
Değişmedi.

## Backend matrisi (018.2 + 018.3 birleşik)
| Backend | Opt-in kapalı | Opt-in açık + kısa obs | Opt-in açık + uzun obs |
|---|---|---|---|
| stub | 018.1 trim | dokunma | stub özet (deterministik) |
| claude | 018.1 trim | dokunma | **real _call_claude** (018.3) |
| anthropic | 018.1 trim | dokunma | **real _call_anthropic** (018.2) |
| acp | 018.1 trim | dokunma | **real _call_acp** (018.3) |

## Cost etkisi
Her real çağrı ekstra bir process/oturum + prompt tokenları demek.
- Claude: her uzun obs için bir subprocess `claude --print`.
- ACP: her uzun obs için yeni Popen + initialize + session/new +
  session/prompt. Ağır bir setup — ACP için özet önbelleği düşünülebilir
  (YAGNI şimdilik).
- Anthropic: mevcut `_write_metric_for_data` her çağrıyı jsonl'a yazar
  → `atlas metrics --limit 100` özet çağrılarını da gösterir.

## Kullanım örneği
```bash
# claude backend ile:
$ ATLAS_LLM=claude ATLAS_LLM_OBS_SUMMARIZE=1 \
    atlas run --goal-file build.yaml
# 500 satırlık pytest log'u claude subprocess'ine "özetle" ile
# gönderilir, tek cümlelik özet plan promptuna gömülür.
```

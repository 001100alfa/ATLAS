# 008 — İhtiyaç: LLM planner retry/backoff sarmalayıcısı

## Bağlam
Görev 003 + 003.1 üç LLM backend'ini (claude/anthropic/acp) canlandırdı;
sözleşme: her plan çağrısında **tek deneme**, hata → `LLMPlannerError`.
Ağ dalgalanması, geçici 429/500, ACP subprocess race durumlarında
görev tek çağrıda düşüyor — bütçe/durum kaybı. SPEC 003 Q4'te retry
"Görev 013" olarak ertelenmişti; bu görev o notu kapatır ama minimum
yeterli düzeyde: N deneme + üstel backoff, planner sözleşmesi
değişmez.

## İhtiyaç (tek cümle)
`make_planner(...)` çıktısına opsiyonel bir retry sarmalayıcı geçirilebilsin;
`LLMPlannerError` yakalanıp `ATLAS_LLM_RETRIES` (varsayılan 0 = kapalı)
kadar tekrar denensin, denemeler arası üstel backoff (`ATLAS_LLM_BACKOFF`
saniye taban) beklensin, son denemede yine hata → raise.

## Ölçülebilir Başarı
- **M1 — Sözleşme değişmez:** Sarmalayıcı yine `Callable[[str, list], str]`
  döner. `run_loop` fark etmez; mevcut testler geçer.
- **M2 — Env varsayılan kapalı:** `ATLAS_LLM_RETRIES` set edilmemişse
  veya `0` ise sarmalayıcı **tek deneme** — mevcut davranış bit-uyumlu.
- **M3 — Retry geometrisi:** `retries=3` → toplam 4 deneme (ilk + 3 retry).
  Denemeler arası uyku `backoff * (2 ** attempt)` — 1s, 2s, 4s (backoff=1).
- **M4 — Hata seçiciliği:** Sadece `LLMPlannerError` yakalanır. Başka
  istisna (KeyboardInterrupt, ValueError, mypy hatası, PlannerExhaustedError)
  sarmadan geçer.
- **M5 — Son deneme raise:** Tüm denemeler başarısızsa **son hata**
  raise edilir (`from` chain ile son hatayı gösterir, önceki denemeleri
  değil).
- **M6 — CLI entegrasyonu:** `cli.py::_cmd_run_goal` `make_planner`
  çıktısını `_maybe_wrap_retry(planner)` ile sarar. Env kapalıysa
  kimlik-geçiş (`return planner`).
- **M7 — Trace görünürlüğü:** `ATLAS_LLM_TRACE=1` env'inde her retry
  stderr'e `[retry] deneme N/M başarısız: <mesaj>` yazar. Kapalı
  varsayılan (test gürültüsü yok).
- **M8 — Test kapsamı:** 8-10 test (env kapalı, 1 retry başarılı, tüm
  retry başarısız, geometrik backoff, PlannerExhausted geçer, trace
  formatı). CLI'de 1 in-process test. Coverage ≥ %90.
- **M9 — DECISIONS:** [KARAR] retry planner-**dışı** neden sarmalayıcı,
  sözleşmeyi neden korumak önemli.

## Kapsam DIŞI
- Jitter (rastgele salınım) — deterministik backoff yeter; jitter Görev 013+.
- Retry içinde farklı backend'e geçiş — protokol dışı.
- HTTP-Header tabanlı retry-after (anthropic 429) — Görev 011+.
- Otomatik quota kesme (bütçe aşımı) — Görev 011 token cost + 013.

## Kısıt
- `Planner`, `make_planner`, `PlannerExhaustedError`, `LLMPlannerError`
  imzaları değişmez.
- stdlib-only: `time`, `os`, `functools`.
- `time.sleep` monkeypatch edilebilir (test).
- Türkçe log/hata; istisna adları `*Error` sonekli.

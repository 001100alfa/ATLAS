# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (8. tur — 016.2+021.1+021.2+022+023+024 + merge/push/temizlik)
**Branch:** `main` (origin/main ile senkron — `4553d0a`)
**Working tree:** temiz
**Durum:** 6 aşama tamamlandı, 7 lineer commit main'e ff-merge + push
edildi (`71d644e..4553d0a`), 6 feature branch silindi. 518/518 test
yeşil, coverage %90 üstünde, mypy strict + ruff + scan temiz.
Bilinen flaky yok.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 8. tur)

Sıra ile 6 iş tamamlandı, her biri kendi branch'inde tek commit,
zincirleme (`016.2 → 021.1 → 021.2 → 022 → 023 → 024`); sonrasında
main'e lineer ff-merge + push + temizlik.

1. **Görev 016.2** — ACP `session/request_permission` (`0b534f7`)
   - `_acp_handle_client_request` dallanma; `_acp_permission_response`
     ~50 sat.
   - Read tool → `allow_once`; write/bilinmeyen → `reject` (savunmalı).
   - `params.options` içinden eşleşen optionId; yoksa sabit fallback.
   - +4 test.

2. **Görev 021.1** — `atlas doctor --json` (`9f0f5bf`)
   - `_collect_doctor_report()` veri toplama refactor'ü — sunumdan
     ayrık.
   - `--json` → tek satır JSON (alan isimleri env değişkeni adları).
   - `warnings` string listesi. API key mask JSON'da da uygulanır.
   - +4 test.

3. **Görev 021.2** — `atlas doctor --ping` (`78716cf`)
   - Anthropic'e minimum "hello" request (max_tokens=8, timeout 10s
     sabit).
   - Insan formatta `[Ping]` bölümü; JSON'da `ping` alanı.
   - Hata warnings + exit 0 (021 kalıbı).
   - +4 test.

4. **Görev 022** — `.env` otomatik yükleme (`904a551`)
   - `_load_dotenv()` stdlib manuel parser ~25 sat.
   - Shell env override edilmez (dotenv sadece eksikleri doldurur).
   - `ATLAS_DOTENV` env yolu override.
   - +7 test.

5. **Görev 023** — cache-hit metrikleri (`9fbbafd`)
   - `.atlas/metrics.jsonl` her anthropic çağrısı sonrası append
     (`{ts, in, out, cache_c, cache_r, cost}`); yazım hatası sessiz.
   - `atlas metrics [--limit N] [--json]` — toplam tokens +
     cache-hit oranı % + tahmini cost.
   - Streaming (019) yolu da metric yazar.
   - +7 test.

6. **Görev 024** — `atlas dashboard` (`f8db09c`)
   - `.atlas/audit.jsonl` heuristik run tespiti (plan/dry_run
     başlangıç, done/max_steps/denied/llm_error bitiş).
   - `.atlas/metrics.jsonl`'dan zaman aralığındaki cost eşleşmesi.
   - İlk satır: denetim zincir sağlığı (`AuditLog.verify`).
   - +6 test.

7. **Merge + push + temizlik**
   - `git merge --ff-only feat/024-dashboard` → 7 commit lineer
     main'e (`4553d0a`), merge commit YOK.
   - `git push origin main` → `71d644e..4553d0a` uzağa gitti.
   - 6 feature branch silindi (`feat/016.2-acp-permission`,
     `feat/021.1-doctor-json`, `feat/021.2-doctor-ping`,
     `feat/022-dotenv-autoload`, `feat/023-cache-metrics`,
     `feat/024-dashboard`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal devam adayları:

- **Görev 016.3 — ACP interaktif permission dialogu:** opt-in
  `ATLAS_ACP_INTERACTIVE=1`.
- **Görev 018.1 — LLM ile gözlem özetleme:** uzun stderr → 3 satır özet.
- **Görev 019.1 — ACP streaming:** ACP session_prompt yanıtları
  streaming.
- **Görev 025 — Prompt engineering skill:** pipeline/tasks üzerine
  yaygın prompt kalıpları toplayan skill.
- **Görev 026 — Docker/podman sandbox:** shell action'ı container'da
  çalıştır.
- **Görev 027 — `atlas replay <run-id>`:** dashboard'daki bir run'ı
  aynı prompt ile yeniden çalıştır (test/regresyon).

Ya da başka bir öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (4553d0a) = main (4553d0a) ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 7 commit (2026-07-29 8. tur):**
```
4553d0a docs: DEVAM_NOKTASI.md — 8. tur kapanis
f8db09c feat(024): atlas dashboard
9fbbafd feat(023): cache-hit metrikleri
904a551 feat(022): .env otomatik yukleme
78716cf feat(021.2): atlas doctor --ping
9f0f5bf feat(021.1): atlas doctor --json
0b534f7 feat(016.2): ACP session/request_permission
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 518 passed
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI komutları (bu turda):**
- `atlas doctor --json` (021.1)
- `atlas doctor --ping` (021.2)
- `atlas metrics [--limit N] [--json]` (023)
- `atlas dashboard [--limit N] [--json]` (024)

**Env sözleşmesi (kümülatif):**
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM` | `stub` \| `claude` \| `anthropic` \| `acp` |
| `ATLAS_LLM_TIMEOUT` | ortak timeout (varsayılan 60 sn) |
| `ATLAS_LLM_CLAUDE_BIN` | claude override |
| `ANTHROPIC_API_KEY` | anthropic zorunlu |
| `ATLAS_LLM_MODEL` | anthropic model — `Goal.llm_model` üstünde |
| `ATLAS_LLM_ANTHROPIC_URL` | anthropic URL override |
| `ATLAS_LLM_ACP_BIN` | acp zorunlu |
| `ATLAS_LLM_ACP_ARGS` | acp extra argv |
| `ATLAS_CONTEXT` | `on` (varsayılan) \| `off` |
| `ATLAS_LLM_RETRIES` | retry sayısı (varsayılan 0 = kapalı) |
| `ATLAS_LLM_BACKOFF` | üstel taban saniye (varsayılan 1.0) |
| `ATLAS_LLM_JITTER` | jitter üst-sınır saniye (varsayılan 0.0) |
| `ATLAS_LLM_TRACE=1` | retry stderr + anthropic usage stderr |
| `ATLAS_LLM_PRICE_IN` | anthropic input per million USD |
| `ATLAS_LLM_PRICE_OUT` | anthropic output per million USD |
| `ATLAS_LLM_OBS_CHARS` | gözlem char üst sınır (varsayılan 200) |
| `ATLAS_ARCHIVE_AGE_DAYS` | `--auto` yaş eşiği (varsayılan 7) |
| `ATLAS_DOTENV` | `.env` yolu override (varsayılan `./.env`) |
| `ATLAS_METRICS` | metrics.jsonl yolu (varsayılan `.atlas/metrics.jsonl`) |

**Exit kodları (değişmedi):** 0/2/3/4/5/6/7.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py::{run_loop, Action, Judge, LoopResult,
  StepKind, BudgetExceededError, CallBudget}` — dokunulmadı.
- `orchestrator/planner.py::{Planner, make_planner,
  make_retrying_planner, PlannerExhaustedError, LLMPlannerError,
  RetryAfterError}` — imzalar korundu. `_call_anthropic` yalnız
  yan-etki eklendi (metric yaz), imza değişmedi.
- `orchestrator/goals.py::Goal` — dokunulmadı.
- `AuditLog` sözleşmesi (record/verify) — dokunulmadı.
- `atlas doctor` (021) mevcut alt-komut korundu; yeni bayraklar
  eklendi (`--json`, `--ping`).

**Bilinen flaky:** yok.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-29 altında **27 giriş bloğu**
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,02-spec,09-ship}.md`
4. Değişecek modülün üstündeki docstring

---

## Kapanış Notları

- 518 test yeşil (bu turun baseline'ı 486 → +32; oturum başı 319 → +199)
- 7 lineer commit main'e alındı, uzağa push edildi, 6 feature branch
  silindi (kullanıcı açık onayıyla)
- Uncommitted değişiklik yok, working tree temiz
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) —
  dokunulmadı
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB) —
  yenilenmemedi (kapsam dışı)
- DECISIONS.md 2026-07-29 altında **27 giriş bloğu** birikti

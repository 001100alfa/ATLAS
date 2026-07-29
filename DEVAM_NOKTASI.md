# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (9. tur — 016.3+018.1+019.1+025+026+027)
**Branch:** `feat/027-atlas-replay` (main'e ff-merge onayı bekliyor)
**Working tree:** temiz
**Durum:** 6 aşama tamamlandı, 6 lineer commit main'in üstünde
zincirleme hazır. 545/545 test yeşil (baseline 518 → +27), coverage
%90 üstünde, mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 9. tur)

Sıra ile 6 iş tamamlandı, zincirleme (`016.3 → 018.1 → 019.1 → 025 →
026 → 027`).

1. **Görev 016.3** — ACP interaktif permission (`c147ed5`)
   - `ATLAS_ACP_INTERACTIVE=1` env → stdin y/n prompt.
   - Fail-safe: EOF/KeyboardInterrupt → 016.2 auto-karar.
   - +4 test.

2. **Görev 018.1** — gözlem head+tail keep (`3d0805b`)
   - `ATLAS_LLM_OBS_HEAD` + `ATLAS_LLM_OBS_TAIL` (varsayılan 100/100).
   - Uzun stderr'ın sonundaki hata mesajı kaybolmaz.
   - Mantıksız env fallback → 018 davranışı.
   - +8 test.

3. **Görev 019.1** — ACP streaming ilk newline'da kes (`11c9634`)
   - Anthropic streaming (019) ile birebir simetri.
   - Boş newline devam, süreç kill korunur.
   - +3 test.

4. **Görev 025** — Prompt engineering skill (`903137d`)
   - `skills/engineering/prompt/SKILL.md` ~250 sat Türkçe rehber.
   - Görev-tipi kalıpları (kod, test, DXF, EN 1993) + karşı örnekler
     + cost workflow.
   - Test/coverage yok — dokümantasyon.

5. **Görev 026** — Sandbox iyileştirme (Docker YOK) (`52047a3`)
   - `_scrub_env` whitelist — API key sızmaz.
   - `ATLAS_SANDBOX_PATH` PATH override.
   - `ATLAS_SANDBOX_TIMEOUT` timeout env-ayarlı.
   - stderr observation'da `err=<...>`.
   - Docker yasak, portable stdlib-only. Unix `resource` / Windows Job
     opt-in 026.1/026.2.
   - +6 test.

6. **Görev 027** — atlas replay (`5ef9606`)
   - YAML kopya `.atlas/runs/<goal-id>.yaml`.
   - `atlas replay <run-id> [--new-run-id X]`.
   - `ATLAS_RUNS_DIR` env yol override.
   - Dashboard tablosuna `run_id` kolonu (`.atlas/runs/*.yaml` mtime
     desc + zip runs).
   - +6 test.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Merge + push.** 6 lineer commit main'in üstünde hazır:

```
main (c48882b) ← origin/main (senkron)
     ↑
     c147ed5 feat(016.3): ACP interaktif permission
     3d0805b feat(018.1): gözlem head+tail keep
     11c9634 feat(019.1): ACP streaming ilk newline'da kes
     903137d feat(025): skills/engineering/prompt SKILL.md
     52047a3 feat(026): sandbox iyileştirme (Docker YOK)
     5ef9606 feat(027): atlas replay + YAML kopya
```

Önerilen yol:

```bash
git checkout main
git merge --ff-only feat/027-atlas-replay   # 6 commit lineer
git push origin main
git branch -d feat/016.3-acp-interactive feat/018.1-obs-headtail \
             feat/019.1-acp-streaming feat/025-prompt-engineering-skill \
             feat/026-sandbox-hardening feat/027-atlas-replay
```

Alternatif — yeni görev seçilebilir. Doğal devamlar:

- **Görev 018.2 — LLM ile gerçek gözlem özetleme:** opt-in
  `Goal.obs_summarize`, ekstra LLM çağrısı.
- **Görev 026.1 — Unix `resource` limits:** RLIMIT_CPU, RLIMIT_AS
  opt-in.
- **Görev 026.2 — Windows Job Objects:** memory + process limits.
- **Görev 028 — `atlas replay --list`:** kayıtlı run'ları listeler.
- **Görev 029 — Cache-hit alarm:** `atlas metrics --alert 20`:
  cache-hit < %X ise stderr uyarı + exit != 0.
- **Görev 030 — Multi-goal batch:** `atlas run --goal-file A.yaml
  B.yaml C.yaml` — sıralı çalıştırma.

---

## Hızlı Bağlam

**Env sözleşmesi (kümülatif, bu turda eklenenler ★):**
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM` | `stub` \| `claude` \| `anthropic` \| `acp` |
| `ATLAS_LLM_TIMEOUT` | ortak timeout (varsayılan 60 sn) |
| `ATLAS_LLM_CLAUDE_BIN` | claude override |
| `ANTHROPIC_API_KEY` | anthropic zorunlu |
| `ATLAS_LLM_MODEL` | anthropic model |
| `ATLAS_LLM_ANTHROPIC_URL` | anthropic URL override |
| `ATLAS_LLM_ACP_BIN` | acp zorunlu |
| `ATLAS_LLM_ACP_ARGS` | acp extra argv |
| `ATLAS_CONTEXT` | `on` (varsayılan) \| `off` |
| `ATLAS_ACP_INTERACTIVE=1` ★ | **016.3** — permission stdin sordur |
| `ATLAS_LLM_RETRIES` | retry sayısı (varsayılan 0) |
| `ATLAS_LLM_BACKOFF` | üstel taban saniye (1.0) |
| `ATLAS_LLM_JITTER` | jitter saniye (0.0) |
| `ATLAS_LLM_TRACE=1` | retry+usage stderr |
| `ATLAS_LLM_PRICE_IN` | anthropic input per million USD |
| `ATLAS_LLM_PRICE_OUT` | anthropic output per million USD |
| `ATLAS_LLM_OBS_CHARS` | gözlem char üst sınır (varsayılan 200) |
| `ATLAS_LLM_OBS_HEAD` ★ | **018.1** — head char (100) |
| `ATLAS_LLM_OBS_TAIL` ★ | **018.1** — tail char (100) |
| `ATLAS_ARCHIVE_AGE_DAYS` | `--auto` yaş eşiği (7) |
| `ATLAS_DOTENV` | `.env` yolu override |
| `ATLAS_METRICS` | metrics.jsonl yolu |
| `ATLAS_SANDBOX_PATH` ★ | **026** — sandbox subprocess PATH |
| `ATLAS_SANDBOX_TIMEOUT` ★ | **026** — sandbox timeout sn (10.0) |
| `ATLAS_RUNS_DIR` ★ | **027** — replay kopyaları yol (`.atlas/runs`) |

**Exit kodları (değişmedi):** 0/2/3/4/5/6/7.

**Yeni CLI komutları (bu turda):**
- `atlas replay <run-id> [--new-run-id X] [--dry-run]` (027)

**Yeni skill:**
- `skills/engineering/prompt/SKILL.md` (025)

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py`, `orchestrator/goals.py`, `AuditLog` — dokunulmadı.
- `orchestrator/planner.py::{Planner, make_planner, LLMPlannerError,
  RetryAfterError}` — imzalar korundu.
- `orchestrator/actions.py::{make_action, Action, ActionDeniedError}` —
  imzalar korundu; `_shell` yalnız yeni env/timeout parametreleri.
- `atlas run` sözleşmesi + mevcut alt-komutlar — dokunulmadı; yeni
  `atlas replay` eklendi.

**Bilinen flaky:** yok.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-29 altında **33 giriş bloğu**
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,02-spec,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. Yeni: `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 545 test yeşil (bu turun baseline'ı 518 → +27; oturum başı 319 → +226)
- 6 lineer commit `feat/027-atlas-replay` ucunda; merge stratejisi
  user'a bağlı
- Uncommitted değişiklik yok, working tree temiz
- Docker YASAK (kullanıcı direktifi 026'da) — portable stdlib-only
  sandbox iyileştirmesi
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında — dokunulmadı
- DECISIONS.md 2026-07-29 altında **33 giriş bloğu** birikti

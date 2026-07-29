# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (6. tur — 013+010.1+014+015+016+017)
**Branch:** `feat/017-archive-auto` (main'e ff-merge onayı bekliyor)
**Working tree:** temiz
**Durum:** 6 aşama tamamlandı, 6 lineer commit main'in üstünde
zincirleme hazır. 444/444 test yeşil (baseline 420 → +24), coverage
%90 üstünde, mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 6. tur)

Sıra ile 6 iş tamamlandı, her biri kendi branch'inde tek commit,
zincirleme (`013 → 010.1 → 014 → 015 → 016 → 017`).

1. **Görev 013** — CallBudget'a token maliyeti entegrasyonu (`057df31`)
   - `CallBudget.charge_tokens(in_tok, out_tok, price_in, price_out)`
     — cost = `in * price_in / 1e6 + out * price_out / 1e6`.
   - Aşarsa `BudgetExceededError` (mevcut sınıf).
   - Fiyat 0/negatif → no-op (011 fail-safe kalıbı).
   - `_call_anthropic(..., on_usage: Callable | None = None)` keyword-only.
   - `_anthropic_planner` + `make_planner` `on_usage` iletir.
   - CLI `_cmd_run_goal`: `_read_llm_prices()` + `_on_usage =
     budget.charge_tokens` bind.
   - 9 birim + 3 backend test = +12 test.

2. **Görev 010.1** — claude subprocess `--append-system-prompt` (`7135d71`)
   - `goal.llm_prompt` claude'a **argv** üzerinden geçer;
     `include_system=False` ile gövde temiz kalır.
   - Anthropic body.system alanı ile birebir simetri.
   - 003.2 test kalıbı 010.1 kalıbına dönüşüm; +1 test.

3. **Görev 014** — Retry jitter + `Retry-After` header (`2840da3`)
   - `ATLAS_LLM_JITTER` env — `[0, jitter)` uniform backoff üstüne.
   - `RetryAfterError` (`LLMPlannerError` alt sınıfı, attribute
     `retry_after_s: float`).
   - `_call_anthropic` HTTPError'da `Retry-After` başlığı varsa
     `RetryAfterError`; sarmalayıcı backoff yerine header saniyesini
     kullanır (jitter eklenmez).
   - +10 test.

4. **Görev 015** — Anthropic prompt caching (`00dff15`)
   - `Goal.prompt_cache: bool = False` opsiyonel alan.
   - True + `llm_prompt` → anthropic body.system **bloklar listesi** +
     `cache_control: {"type": "ephemeral"}` (5 dk cache).
   - claude/acp alanı yok sayar.
   - +7 test.

5. **Görev 016** — ACP `tool_call` açık red (`08ccfac`)
   - `session/update` `sessionUpdate == "tool_call"` / `"tool_call_update"`
     → `LLMPlannerError("acp: tool-use şu an desteklenmiyor")`.
   - Süreç `_acp_teardown` bloğunda kill.
   - Bilinmeyen sessionUpdate hâlâ sessizce atlanır (forward-compat).
   - +3 test.

6. **Görev 017** — `atlas archive --all --auto` yaş filtresi (`ee868fe`)
   - `--auto` bayrağı `ship.md` `st_mtime`'ı `ATLAS_ARCHIVE_AGE_DAYS`
     (varsayılan 7) günden eski görevleri seçer.
   - 012 mevcut `--all` yolu hiç değişmedi.
   - Çift kapı (`--apply --yes`) korunur.
   - +4 test.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Merge + push.** 6 lineer commit main'in üstünde hazır:

```
main (4edfdbe) ← origin/main (senkron)
     ↑
     057df31 feat(013): CallBudget.charge_tokens
     7135d71 feat(010.1): claude --append-system-prompt
     2840da3 feat(014): retry jitter + Retry-After
     00dff15 feat(015): Anthropic prompt caching
     08ccfac feat(016): ACP tool_call/tool_call_update açık red
     ee868fe feat(017): archive --all --auto yaş filtresi
```

Önerilen yol:

```bash
git checkout main
git merge --ff-only feat/017-archive-auto   # 6 commit lineer
git push origin main
git branch -d feat/013-callbudget-tokens feat/010.1-claude-system-arg \
             feat/014-retry-jitter-header feat/015-anthropic-cache \
             feat/016-acp-tool-reject feat/017-archive-auto
```

Alternatif — merge etmeden yeni görev seçilebilir. Doğal devamlar:

- **Görev 015.1 — Cache-hit token indirimi:** 013 fiyat + 015 cache
  kesişimi; `cache_creation_input_tokens` vs `cache_read_input_tokens`
  Anthropic response'ta ayrı; farklı ücretlendirme.
- **Görev 016.1 — ACP tool-use tam:** MCP forwarding + izin dialog'u +
  gerçek tool yürütme (büyük iş).
- **Görev 018 — Gözlem uzunluk kırpma:** `_format_prompt` prompt
  şişmesin (obs 200 char şu an; belki dinamik).
- **Görev 019 — Anthropic streaming:** ilk chunk gelince plan
  raporla (uzun response'larda hız).
- **Görev 020 — `atlas run --dry-run`:** planner çıktısını göster,
  action yürütme (rehearsal).

---

## Hızlı Bağlam

**Env sözleşmesi (kümülatif, bu turda eklenenler ★):**
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM` | `stub` \| `claude` \| `anthropic` \| `acp` \| bilinmiyor |
| `ATLAS_LLM_TIMEOUT` | ortak timeout (varsayılan 60 sn) |
| `ATLAS_LLM_CLAUDE_BIN` | claude override |
| `ANTHROPIC_API_KEY` | anthropic zorunlu |
| `ATLAS_LLM_MODEL` | anthropic model — `Goal.llm_model` üstünde |
| `ATLAS_LLM_ANTHROPIC_URL` | anthropic URL override |
| `ATLAS_LLM_ACP_BIN` | acp zorunlu |
| `ATLAS_LLM_ACP_ARGS` | acp extra argv (shlex) |
| `ATLAS_CONTEXT` | `on` (varsayılan) \| `off` |
| `ATLAS_LLM_RETRIES` | retry sayısı (varsayılan 0 = kapalı) |
| `ATLAS_LLM_BACKOFF` | üstel taban saniye (varsayılan 1.0) |
| `ATLAS_LLM_JITTER` ★ | **014** — jitter üst-sınır saniye (varsayılan 0.0) |
| `ATLAS_LLM_TRACE=1` | retry stderr + anthropic usage stderr |
| `ATLAS_LLM_PRICE_IN` | anthropic input per million USD |
| `ATLAS_LLM_PRICE_OUT` | anthropic output per million USD |
| `ATLAS_ARCHIVE_AGE_DAYS` ★ | **017** — `--auto` yaş eşiği (varsayılan 7) |

**Exit kodları (değişmedi):** 0/2/3/4/5/6/7.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py::{run_loop, Action, Judge, LoopResult, StepKind,
  BudgetExceededError}` — dokunulmadı; `CallBudget` **genişledi** ama
  mevcut alanlar + `charge()` sözleşmesi korundu.
- `orchestrator/planner.py::{Planner, make_planner, make_retrying_planner,
  PlannerExhaustedError, LLMPlannerError}` — imzalar korundu; yeni
  `RetryAfterError` (LLMPlannerError alt sınıfı, LSP uyumlu).
- `orchestrator/goals.py::Goal` — yeni alanlar `prompt_cache: bool =
  False` opsiyonel default'lu (003.2 kalıbı).
- `atlas archive` (007/012) — sözleşme korundu; yeni `--auto`
  daraltıcı bayrak.
- `_call_anthropic`, `_format_prompt`, `_anthropic_planner` — yeni
  parametreler **keyword-only + default** → eski çağrılar etkilenmez.

**Bilinen flaky:** yok.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-29 altında **15 giriş bloğu** (003.1, 003.2,
   007, flaky, 008, 009, 010, 011, 012, 013, 010.1, 014, 015, 016, 017)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,02-spec,09-ship}.md`
4. Değişecek modülün üstündeki docstring

---

## Kapanış Notları

- 444 test yeşil (bu turun baseline'ı 420 → +24; oturum başı 319 → +125)
- 6 lineer commit `feat/017-archive-auto` ucunda; merge stratejisi
  user'a bağlı
- Uncommitted değişiklik yok, working tree temiz
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) —
  dokunulmadı
- DECISIONS.md 2026-07-29 altında **15 giriş bloğu** birikti (bu tur
  itibarıyla): 003.1, 003.2, 007, flaky, 008, 009, 010, 011, 012, 013,
  010.1, 014, 015, 016, 017

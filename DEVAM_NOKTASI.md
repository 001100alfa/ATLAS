# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (5. tur — 008+009+010+011+012 + merge/push/temizlik)
**Branch:** `main` (origin/main ile senkron — `f2caf33`)
**Working tree:** temiz
**Durum:** 5 aşama tamamlandı, 6 lineer commit main'e ff-merge + push
edildi (`a0f16cd..f2caf33`), 5 feature branch silindi. 407/407 test
yeşil, coverage %93.69, mypy strict + ruff + scan temiz. Bilinen
flaky yok.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 5. tur)

Sıra ile 5 iş tamamlandı, her biri kendi branch'inde tek commit,
zincirleme (`008 → 009 → 010 → 011 → 012`); sonrasında main'e
lineer ff-merge + push + temizlik.

1. **Görev 008** — LLM retry/backoff sarmalayıcı (`afe2fcd`)
   - `make_retrying_planner(inner, retries, backoff_s)` — `LLMPlannerError`
     yakala, `backoff * 2**attempt` üstel bekleme, `1 + retries` deneme.
   - Env: `ATLAS_LLM_RETRIES` (0 = kapalı), `ATLAS_LLM_BACKOFF` (1.0 sn),
     `ATLAS_LLM_TRACE=1` (retry stderr'a).
   - `retries <= 0` → **kimlik-geçiş** (`is inner`). Sözleşme değişmez.
   - CLI: `_cmd_run_goal` `make_retrying_planner` ile sarar.
   - 15 birim + 1 CLI test.

2. **Görev 009** — `Goal.llm_model` opsiyonel alanı (`bf15b45`)
   - YAML'da model bildir; öncelik: `goal.llm_model` > `ATLAS_LLM_MODEL`
     env > `_DEFAULT_ANTHROPIC_MODEL`.
   - 003.2 kalıbıyla simetrik (boş string → None, tip yanlış → SpecError).
   - claude/acp backend'ler yok sayar (protokolleri farklı; ertelendi).
   - +8 test.

3. **Görev 010** — Anthropic system rolü ayrımı (`07596b2`)
   - `goal.llm_prompt` anthropic body.system alanına gider; messages
     sadece ATLAS varsayılan gövdesi (kısıt + görev + context + gözlem).
   - `_format_prompt(..., include_system=False)` keyword; anthropic
     backend geçirir. Diğerleri varsayılan (True) → prepend korundu.
   - Model system'i user'dan daha güçlü izler → persona kilidi.
   - +2 test.

4. **Görev 011** — Token cost (report-only) (`8685a72`)
   - Anthropic response `usage.input_tokens` + `output_tokens` yakalanır;
     `ATLAS_LLM_TRACE=1` env'inde stderr'a `[llm] anthropic tokens:
     in=N out=N cost≈$X.XXXXXX`.
   - `ATLAS_LLM_PRICE_IN` + `ATLAS_LLM_PRICE_OUT` per million USD;
     parse hatası → `cost≈?` fail-safe.
   - CallBudget entegrasyonu **kapsam DIŞI** (Görev 013 rezerv).
   - +5 test.

5. **Görev 012** — `atlas archive --all` toplu arşivleme (`af353e6`)
   - Aday: `pipeline/tasks/*/09-ship.md` olanlar.
   - Dry-run varsayılan; `--apply --yes` **ikili onay** (çift kapı);
     `--yes` yoksa exit 2.
   - Fail-fast: ilk hata → dur + rapor (succeeded / failed / skipped
     listesi). Kısmi başarı görünür.
   - Tekil yol (007) korundu — `task nargs="?"`, mevcut 6 test yeşil.
   - +5 test.

6. **Merge + push + temizlik**
   - `git merge --ff-only feat/012-archive-all` → 6 commit lineer
     main'e (`f2caf33`), merge commit YOK.
   - `git push origin main` → `a0f16cd..f2caf33` uzağa gitti.
   - 5 feature branch silindi (`feat/008-retry-backoff`,
     `feat/009-llm-model`, `feat/010-anthropic-system-role`,
     `feat/011-token-cost`, `feat/012-archive-all`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok; 008/009/010/011/012
kapandı. Doğal devam adayları:

- **Görev 013 — CallBudget'a token→kredi entegrasyonu:** 011'in
  doğal genişlemesi; retry (008) + fiyat (011) kesişimi. `CallBudget`
  sözleşmesine token maliyeti eklenir; otomatik quota kesme (bütçe
  aşımı → sıradaki plan iptal).
- **Görev 010.1 — claude subprocess `--system` argümanı:** 010'un
  claude backend'e uzanması. Şu an claude prepend, anthropic system;
  simetri için claude da native system desteklemeli.
- **Görev 014 — Retry jitter + `Retry-After` header'ı:** 008'in
  üstüne gelen politika iyileştirmesi. Anthropic 429 response'unda
  `Retry-After` başlığı verilirse ona uy.
- **Görev 015 — Anthropic prompt caching:** 011 üstüne fiyat indirimi.
  Sistem promptu `cache_control: {"type": "ephemeral"}` ile 5 dk cache.
- **Görev 016 — ACP tool-use ilk aşama:** 003.1'in `agent_message_chunk`
  toplama alt kümesini `tool_call` işleme ile genişletme.
- **Görev 017 — Otomatik `atlas archive --all` cron/hook:** 012'nin
  operasyonel entegrasyonu; `atlas run` sonu ship.md yazıldığında
  arka planda arşive alma teklifi.

Ya da başka bir öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (f2caf33) = main (f2caf33) ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 6 commit (2026-07-29 5. tur):**
```
f2caf33 docs: DEVAM_NOKTASI.md — 5. tur (008..012) kapanis
af353e6 feat(012): atlas archive --all toplu arsivleme
8685a72 feat(011): anthropic token usage trace (report-only)
07596b2 feat(010): Anthropic system rolu ayrimi (llm_prompt -> body.system)
bf15b45 feat(009): Goal.llm_model opsiyonel alani
afe2fcd feat(008): LLM planner retry/backoff sarmalayici
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 407 passed; coverage %93.69
uv run mypy src                # 25 dosya, temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Env sözleşmesi (kümülatif, bu turda eklenenler ★):**
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM` | `stub` \| `claude` \| `anthropic` \| `acp` \| bilinmiyor |
| `ATLAS_LLM_TIMEOUT` | ortak subprocess/HTTPS timeout (varsayılan 60 sn) |
| `ATLAS_LLM_CLAUDE_BIN` | claude override |
| `ANTHROPIC_API_KEY` | anthropic zorunlu |
| `ATLAS_LLM_MODEL` | anthropic model — 009'da `Goal.llm_model` **üstünde** |
| `ATLAS_LLM_ANTHROPIC_URL` | anthropic URL override (test/vekil) |
| `ATLAS_LLM_ACP_BIN` | acp zorunlu |
| `ATLAS_LLM_ACP_ARGS` | acp extra argv (shlex) |
| `ATLAS_CONTEXT` | `on` (varsayılan) \| `off` (SPEC 006) |
| `ATLAS_LLM_RETRIES` ★ | **008** — retry sayısı (varsayılan 0 = kapalı) |
| `ATLAS_LLM_BACKOFF` ★ | **008** — üstel taban saniye (varsayılan 1.0) |
| `ATLAS_LLM_TRACE=1` ★ | **008+011** — retry stderr + anthropic usage stderr |
| `ATLAS_LLM_PRICE_IN` ★ | **011** — anthropic input per million USD (ops.) |
| `ATLAS_LLM_PRICE_OUT` ★ | **011** — anthropic output per million USD (ops.) |

**Exit kodları (değişmedi):**
- 0 başarı, 2 SPEC/YAML/--yes yok, 3 bütçe, 4 max_steps/planner_exhausted,
  5 action_denied, 6 handler/arşiv hatası, 7 LLM planner hatası

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py::{run_loop, Action, Judge, CallBudget,
  LoopResult, StepKind}` — dokunulmadı
- `orchestrator/planner.py::{Planner, make_planner,
  PlannerExhaustedError, LLMPlannerError}` — imzalar korundu; yeni
  yalnız iç yardımcı + `make_retrying_planner` yan-fabrika
- `orchestrator/goals.py::Goal` — yeni alan `llm_model` opsiyonel
  default'lu (003.2 kalıbı)
- `atlas archive <task>` (SPEC 007) — hiç değişmedi; `--all` yeni ek
  yol (`task nargs="?"` esnetildi)
- `_call_anthropic`, `_format_prompt` — yeni parametreler
  **keyword-only + default'lu** (eski çağrılar etkilenmez)

**Bilinen flaky:** yok.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-29 altında **9 giriş bloğu** (003.1, 003.2,
   007, flaky, 008, 009, 010, 011, 012)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,02-spec,09-ship}.md`
4. Değişecek modülün üstündeki docstring

---

## Kapanış Notları

- 407 test yeşil (bu turun baseline'ı 371 → +36; oturum başı 319 → +88)
- Coverage %93.69
- 6 lineer commit main'e alındı, uzağa push edildi, 5 feature branch
  silindi (kullanıcı açık onayıyla)
- Uncommitted değişiklik yok, working tree temiz
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) —
  dokunulmadı
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB) —
  yenilenmemedi (kapsam dışı)
- DECISIONS.md 2026-07-29 altında **9 giriş bloğu** birikti (bu tur
  itibarıyla): 003.1, 003.2, 007, flaky, 008, 009, 010, 011, 012

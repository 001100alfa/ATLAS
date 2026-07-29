# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (7. tur — 015.1+016.1+018+019+020+021 + merge/push/temizlik)
**Branch:** `main` (origin/main ile senkron — `b6acd19`)
**Working tree:** temiz
**Durum:** 6 aşama tamamlandı, 7 lineer commit main'e ff-merge + push
edildi (`e4445ae..b6acd19`), 6 feature branch silindi. 486/486 test
yeşil, coverage %90 üstünde, mypy strict + ruff + scan temiz.
Bilinen flaky yok.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 7. tur)

Sıra ile 6 iş tamamlandı, her biri kendi branch'inde tek commit,
zincirleme (`015.1 → 016.1 → 018 → 019 → 020 → 021`); sonrasında
main'e lineer ff-merge + push + temizlik.

1. **Görev 015.1** — cache-hit token indirimi (`a66c0b6`)
   - `_CACHE_READ_MULT = 0.1`, `_CACHE_WRITE_MULT = 1.25` sabitleri
     (Anthropic tarifesi).
   - `_extract_usage` **4-tuple** — `(input, output, cache_c, cache_r)`.
   - `_fmt_cost` + `CallBudget.charge_tokens` cache alanları
     `cache_creation`/`cache_read` keyword-only (013 default 0 uyumlu).
   - Trace format: cache varsa `in=N (cache=W r=R) out=M`.
   - `on_usage` callback 2-arg → 4-arg (iç API kırıldı, testler
     güncellendi; public planner sözleşmesi korundu).
   - +10 test.

2. **Görev 016.1** — ACP `fs/read_text_file` minimum (`53545a8`)
   - `_call_acp` dispatcher: request (`method + id`) → cevap;
     notification (`method`, id yok) → 016 yolu (bit-uyumlu).
   - `fs/read_text_file` proje kökü altında güvenli okuma (traversal
     `Path.resolve().relative_to(root)` ile engelli).
   - Yazma/shell metotları → `-32000 not supported`; bilinmeyen →
     `-32601 Method not found` (JSON-RPC standart).
   - +6 test.

3. **Görev 018** — gözlem uzunluk kırpma env (`0c5ed9d`)
   - `ATLAS_LLM_OBS_CHARS` env (varsayılan 200, aralık [1, 2000]).
   - Fail-safe: parse hatası/aralık dışı → 200.
   - Runtime okunur — env değişikliği anında etkili.
   - +9 test.

4. **Görev 019** — Anthropic streaming, opt-in (`50f6d3c`)
   - `Goal.stream: bool = False` opsiyonel.
   - True → request `"stream": true`; SSE parser
     `content_block_delta.text_delta` biriktir; **ilk newline'da kes**
     ve `resp.close()`.
   - `message_start`/`message_delta` usage yakalanır (011/013/015.1
     uyum).
   - +8 test.

5. **Görev 020** — `atlas run --dry-run` rehearsal (`eed0d09`)
   - Planner **gerçek** çağrılır (LLM + cost + audit).
   - Action lambda stub'lanır (`[dry-run] eylem yürütülmedi: <plan>`).
   - Judge sabit True → tek adım sonu done.
   - Audit `("atlas-run", "dry_run", <goal>)` marker.
   - LLM hata yolu (exit 7) korunur.
   - +4 test.

6. **Görev 021** — `atlas doctor` env sağlık özeti (`3ff2acc`)
   - Üç bölüm: `[LLM backend]` / `[Retry & fiyat]` / `[Depolama]`.
   - API key **maskeleme** (`sk-***abc`); tam key stdout'a asla düşmez.
   - Uyarılar `[!]` prefix'iyle: eksik key/bin, bilinmeyen backend.
   - Read-only, exit 0.
   - +5 test.

7. **Merge + push + temizlik**
   - `git merge --ff-only feat/021-atlas-doctor` → 7 commit lineer
     main'e (`b6acd19`), merge commit YOK.
   - `git push origin main` → `e4445ae..b6acd19` uzağa gitti.
   - 6 feature branch silindi (`feat/015.1-cache-hit-discount`,
     `feat/016.1-acp-fs-read`, `feat/018-obs-chars-env`,
     `feat/019-anthropic-streaming`, `feat/020-run-dry-run`,
     `feat/021-atlas-doctor`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok; 015.1/016.1/018/019/020/021
kapandı. Doğal devam adayları:

- **Görev 016.2 — ACP `session/request_permission`:** permission
  dialog handler (auto-allow read).
- **Görev 021.1 — `atlas doctor --json`:** CI/pre-flight uyumlu
  JSON çıktı.
- **Görev 021.2 — LLM ping:** `atlas doctor --ping` küçük "hello"
  ile canlılık kontrolü.
- **Görev 022 — `.env` otomatik yükleme:** `python-dotenv` opsiyonel
  bağımlılık veya elle parser.
- **Görev 023 — Multi-turn cache hit metrikleri:** peş peşe çağrılarda
  cache_read oranı, save %.
- **Görev 024 — Dashboard:** `.atlas/audit.jsonl` özeti + son 10 run
  cost tablosu.

Ya da başka bir öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (b6acd19) = main (b6acd19) ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 7 commit (2026-07-29 7. tur):**
```
b6acd19 docs: DEVAM_NOKTASI.md — 7. tur kapanis
3ff2acc feat(021): atlas doctor env sağlık özeti
eed0d09 feat(020): atlas run --dry-run rehearsal
50f6d3c feat(019): Anthropic streaming (opt-in)
0c5ed9d feat(018): ATLAS_LLM_OBS_CHARS env
53545a8 feat(016.1): ACP fs/read_text_file minimum
a66c0b6 feat(015.1): Anthropic cache-hit token indirimi
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 486 passed
uv run mypy src                # 25 dosya, temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Env sözleşmesi (kümülatif):**
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
| `ATLAS_LLM_JITTER` | jitter üst-sınır saniye (varsayılan 0.0) |
| `ATLAS_LLM_TRACE=1` | retry stderr + anthropic usage stderr |
| `ATLAS_LLM_PRICE_IN` | anthropic input per million USD |
| `ATLAS_LLM_PRICE_OUT` | anthropic output per million USD |
| `ATLAS_LLM_OBS_CHARS` | gözlem char üst sınır (varsayılan 200, aralık [1, 2000]) |
| `ATLAS_ARCHIVE_AGE_DAYS` | `--auto` yaş eşiği (varsayılan 7) |

**Exit kodları (değişmedi):** 0/2/3/4/5/6/7.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py::{run_loop, Action, Judge, LoopResult,
  StepKind, BudgetExceededError}` — dokunulmadı.
  `CallBudget.charge_tokens` cache alanları **keyword-only default=0**
  → 013 çağrıları etkilenmedi.
- `orchestrator/planner.py::{Planner, make_planner,
  make_retrying_planner, PlannerExhaustedError, LLMPlannerError,
  RetryAfterError}` — imzalar korundu; `_extract_usage` iç
  fonksiyon 4-tuple'a genişledi; `on_usage` callback 2-arg → 4-arg
  (013 iç API kırıldı, mevcut test güncellendi).
- `orchestrator/goals.py::Goal` — yeni alan `stream: bool = False`
  opsiyonel default'lu (003.2 kalıbı).
- `atlas run` (SPEC 002/006) — sözleşme korundu; yeni `--dry-run`
  bayrak.
- `_call_anthropic`, `_format_prompt`, `_anthropic_planner` — yeni
  parametreler **keyword-only + default** → eski çağrılar etkilenmez.

**Bilinen flaky:** yok.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-29 altında **21 giriş bloğu** (003.1,
   003.2, 007, flaky, 008, 009, 010, 011, 012, 013, 010.1, 014, 015,
   016, 017, 015.1, 016.1, 018, 019, 020, 021)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,02-spec,09-ship}.md`
4. Değişecek modülün üstündeki docstring

---

## Kapanış Notları

- 486 test yeşil (bu turun baseline'ı 444 → +42; oturum başı 319 → +167)
- 7 lineer commit main'e alındı, uzağa push edildi, 6 feature branch
  silindi (kullanıcı açık onayıyla)
- Uncommitted değişiklik yok, working tree temiz
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) —
  dokunulmadı
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB) —
  yenilenmemedi (kapsam dışı)
- DECISIONS.md 2026-07-29 altında **21 giriş bloğu** birikti

# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (3. tur — merge + push + temizlik)
**Branch:** `main` (origin/main ile senkron)
**Working tree:** temiz
**Durum:** 002 → 004 → 005 → 003 → 006 zinciri **main'e ff merge + push
edildi** (`origin/main = 1a3601f`). 5 feature branch (002/003/004/005/006)
silindi. Test 319/319 yeşil, coverage %94.85, mypy strict + ruff temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 2. + 3. tur)

- 003 (LLM planner) + 006 (auto-context) tamamlandı, 35 yeni test.
- `git checkout main` + `git merge --ff-only feat/006-auto-context` →
  10 commit lineer main'e taşındı (merge commit YOK, temiz history).
- `git push origin main` → 11 commit uzağa gitti (`f93b2d5..1a3601f`),
  branch protection yok.
- 5 feature branch silindi (`feat/002-orkestrator-canlanma`, `feat/003-llm-planner`,
  `feat/004-workflow-handlers`, `feat/005-gbrain-fts`, `feat/006-auto-context`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok; 002/003/004/005/006 kapandı.
Olası yönler (DEVAM_NOKTASI'nde beklenen adı geçmiş görevler):

- **Görev 003.1 — `acp` ve `anthropic` LLM backend'leri:** planner.py'de
  NotImplementedError bekleyen iki backend.
- **Görev 003.2 — YAML'da `Goal.llm_prompt` opsiyonel alanı:** sabit prompt
  yerine görev-başına özelleştirme.
- **Görev 007 — Ne olabilir?** Örn. context'in Judge'a enjekte edilmesi;
  arşivleme handler'ının gerçek arşivlemesi; yeni skills entegrasyonu.
- **Kırık/flaky düzeltme:** `test_doctor_gui.py::test_restore_defaults_to_newest_and_can_pick_by_name`
  Windows mtime granülerliğinde flaky — kalıcı fix (sleep veya bileşik key).

Ya da başka bir öncelik varsa net söyle.

---

## Hızlı Bağlam (yeni oturum için ajanın okuması yeterli)

**Branch grafı:**
```
origin/main (1a3601f) = main (1a3601f) ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme, ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 11 commit (2026-07-29 turu):**
```
d1a7686 docs: DEVAM_NOKTASI.md — 2026-07-29 kapanis
821ffae feat(006): otomatik GBrain context injection
e627d20 feat(003): LLM planner (claude subprocess) + LLMPlannerError + exit 7
fc386d9 docs: DEVAM_NOKTASI.md — 2026-07-28 kapanis
95b7cd6 feat(005): GBrain SQLite-FTS5 indeksi + otomatik reindex
cf63939 feat(004): WorkflowEngine handler kaydi + 3 kanit handler
94d270e feat(002/3.5+3.6+ship): CLI --goal-file entegrasyonu + 10 e2e test
e672980 feat(002/3.3+3.4): planner + judges + 11 test
d5a9693 feat(002/3.2): sandbox jailed actions + 10 test
35570c3 feat(002/3.1): Goal YAML yukleyici + 12 test
```

**Kalite kapıları (referans):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
uv run mypy src
uv run ruff check src tests
uv run atlas scan src
```

**Kritik sözleşme değişmezlikleri (kırma!):**
- `orchestrator/core.py` — `run_loop`, `Action`, `Judge`, `CallBudget`, `LoopResult`
- `orchestrator/planner.py` — `Planner`, `make_planner(goal, context=None)`,
  `PlannerExhaustedError`, `LLMPlannerError`
- `workflows/engine.py` — `WorkflowEngine.register/run`, `WorkflowError`, `StepResult`
- `memory/gbrain.py` — `recall/remember/context_for/log_event` imzaları; `Recall` alanları
- `memory/vault.py` — `Vault` API'si
- `orchestrator/goals.py::Goal` — mevcut alanlar korunur; yeni alanlar
  **opsiyonel default'lu** (2026-07-29: `inject_context`, `context_limit`)

**Exit kodları (mevcut kalıp):**
- `0` başarı, `2` YAML/spec hatası, `3` bütçe, `4` max_steps/planner_exhausted,
  `5` action_denied, `6` handler başarısız / bilinmeyen handler,
  `7` LLM planner hatası (bin yok, timeout, exit!=0, boş cevap) — **2026-07-29**

**Env sözleşmesi (2026-07-29 eklemeler):**
- `ATLAS_LLM` — `stub` (varsayılan) | `claude` | `acp`/`anthropic` (NotImpl)
- `ATLAS_LLM_CLAUDE_BIN` — mutlak yol, opsiyonel
- `ATLAS_LLM_TIMEOUT` — saniye (varsayılan 60)
- `ATLAS_CONTEXT` — `on` (varsayılan) | `off`

**İstisna adlandırma standardı (ruff N818):** tüm `Exception` sınıfları `*Error` sonekli.

**Test yazma kalıbı:**
- subprocess-CLI testleri coverage'ı görmez → `test_cli_direct.py`'de in-process
  `main([...])` çağıran ek test şart (DECISIONS 2026-07-28)
- subprocess.run çağıran test helper'larında **encoding="utf-8", errors="replace"**
  şart — Windows cp1254 locale'da UTF-8 çıktı decode edilmez (DECISIONS 2026-07-29)

**Görev-öncesi zorunlu okuma:**
1. `DECISIONS.md` — en üstteki [KARAR]/[HATA] satırları (2026-07-29)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin varsa `pipeline/tasks/<XXX>/00-need.md` + `02-spec.md`
4. Değişecek modülün üstündeki docstring

**Zorunlu döngü (CLAUDE.md gereği):** SPEC → PLAN → BUILD → TEST → SHIP.
SPEC onayı olmadan kod yazılmaz.

**Bilinen flaky:**
- `test_doctor_gui.py::test_restore_defaults_to_newest_and_can_pick_by_name`
  ilk turda Windows mtime granülerliğine takılabiliyor; ikinci tur geçer.

---

## Kapanış Notları

- Uncommitted değişiklik yok, working tree temiz.
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) — dokunulmadı.
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB).
- Herhangi bir aksama olursa DECISIONS.md 2026-07-29 girdileri tam bağlamı verir.
- Bu turda main güncellendi, uzağa push edildi, 5 feature branch silindi
  (kullanıcı açık onayıyla). origin/main = local main = 1a3601f.

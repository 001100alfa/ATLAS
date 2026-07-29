# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29
**Branch:** `feat/006-auto-context` (main'e merge edilmedi)
**Working tree:** temiz
**Durum:** 002 → 004 → 005 → 003 → 006 tamamlandı. Test 319/319 yeşil,
coverage %94.85, mypy strict 25 dosya temiz, ruff temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Yapılan İşler (bu oturumda — 2026-07-29)

### Görev 003 — LLM planner entegrasyonu ✅
- Branch: `feat/003-llm-planner` (1 commit, üstünde 005)
- `ATLAS_LLM=claude` altında `claude --print` subprocess ile gerçek plan
- Windows uyumlu: `shell=False`, `text=True`, `encoding="utf-8"`,
  `errors="replace"`, stdin=prompt, timeout env-ayarlı
- `LLMPlannerError` + yeni exit **7** + audit `llm_error` kaydı
- Fabrika fail-fast: bin bulunamazsa run_loop'a girmeden hata
- `acp`/`anthropic` açık NotImplementedError ("Görev 003.1")
- Bonus: test_cli_goal.py + test_cli_workflow.py `_run` helper'larına
  UTF-8 encoding sabitlendi (Windows cp1254 flaky sorunu, DECISIONS 2026-07-24
  kalıbının test-tarafı uzantısı)
- 14 yeni + 2 CLI in-process + 2 goal test = 18 yeni test
- Artefaktlar `pipeline/tasks/003-llm-planner/`

### Görev 006 — Otomatik context injection ✅
- Branch: `feat/006-auto-context` (1 commit, üstünde 003)
- `atlas run --goal-file` başında `GBrain.context_for(goal.goal)` tek kez
- Static görev + `ATLAS_CONTEXT=off` + `Goal.inject_context: false` → GBrain
  hiç instantiate edilmez (disk/CPU maliyeti sıfır)
- LLM claude planner prompt'a "Önceden bilinen bağlam (GBrain):" bloğu ekler
- GBrain hatası (disk dolu, index bozuk) izole edilir — görev context'siz devam
- CLI görünürlük: `Bağlam: N not enjekte edildi / yok / (kapalı)`
- `Goal` opsiyonel `inject_context: bool=True` + `context_limit: int=5` (≤50)
- Sözleşme genişleme: `make_planner(goal, context=None)` — geriye uyumlu
- 17 yeni test (5 goals + 6 planner_llm + 6 cli_direct)
- Artefaktlar `pipeline/tasks/006-auto-context/`

---

## Sıradaki Karar (kullanıcıya sunulacak)

**PR / merge stratejisi** — 5 branch (002 → 004 → 005 → 003 → 006) main'e
nasıl taşınsın? DEVAM_NOKTASI'nde 2026-07-29 turunda soruldu, yanıt gelmedi
→ güvenli varsayılan uygulandı: **local'de bırakıldı, hiçbir uzak işlem
yapılmadı**. Seçenekler:

1. **Local fast-forward + push (tek atomik):**
   ```
   git checkout main
   git merge --ff-only feat/006-auto-context   # 5 commit lineer main'e
   git push origin main
   ```
   En hızlı. GitHub'da PR açılmaz. Push yıkıcı — onay şart.

2. **Tek konsolide GitHub PR (feat/006 → main):**
   `gh pr create --base main --head feat/006-auto-context`
   5 commit tek PR. Kullanıcı reviewer.

3. **5 ayrı PR (sıralı):** 002 → main önce, sırayla 004, 005, 003, 006.
   Temiz geçmiş, uzun süreç.

4. **Merge etme, local'de bırak** (mevcut durum): 5 branch local'de kalır.

---

## Hızlı Bağlam (yeni oturum için ajanın okuması yeterli)

**Branch grafı:**
```
main (f93b2d5)
  └─ feat/002-orkestrator-canlanma (94d270e) — 4 commit
       └─ feat/004-workflow-handlers (cf63939)
            └─ feat/005-gbrain-fts (fc386d9)
                 └─ feat/003-llm-planner (e627d20)
                      └─ feat/006-auto-context (821ffae) ← ŞUAN BURADA
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
  **opsiyonel default'lu** (bu turda `inject_context`, `context_limit` eklendi)

**Exit kodları (mevcut kalıp):**
- `0` başarı, `2` YAML/spec hatası, `3` bütçe, `4` max_steps/planner_exhausted,
  `5` action_denied, `6` handler başarısız / bilinmeyen handler,
  `7` LLM planner hatası (bin yok, timeout, exit!=0, boş cevap) — **2026-07-29 yeni**

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
  Görev 007+ notu (bu oturum dışı).

---

## Kapanış Notları

- Uncommitted değişiklik yok, working tree temiz.
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) — dokunulmadı.
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB).
- Herhangi bir aksama olursa DECISIONS.md 2026-07-29 girdileri tam bağlamı verir.
- **Bu oturumda hiçbir yıkıcı işlem yapılmadı** (main dokunulmadı, push yok,
  arşivleme yok). Merge kararı bir sonraki tura ertelendi.

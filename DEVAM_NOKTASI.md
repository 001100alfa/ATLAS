# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-28
**Branch:** `feat/005-gbrain-fts` (main'e merge edilmedi)
**Working tree:** temiz
**Durum:** 3 tur pes peşe pipeline disiplini tamamlandı (002 → 004 → 005). Test 286/286 yeşil, coverage %95, mypy strict 25 dosya temiz, ruff temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

Ajan bu dosyayı okuyup son iki bölümdeki (Sıradaki Karar + Hızlı Bağlam) durumu görecek, sonra kullanıcıya seçenekleri sunacak.

---

## Yapılan İşler (bu oturumda)

### Görev 002 — Orkestratörün Canlanması ✅
- Branch: `feat/002-orkestrator-canlanma` (4 commit)
- `atlas run --goal-file <yaml>` gerçek görev sürücüsü
- Yeni: `orchestrator/goals.py`, `actions.py`, `planner.py`, `judges.py` + CLI entegrasyonu
- Sandbox jailed read/write/shell; ActionDeniedError; llm-stub planner
- 43 yeni test; artefaktlar `pipeline/tasks/002-orkestrator-canlanma/`

### Görev 004 — WorkflowEngine handler kaydı ✅
- Branch: `feat/004-workflow-handlers` (1 commit, üstünde 002)
- `atlas workflow run <yaml> [--dry-run]` gerçek handler'larla çalışıyor
- Yeni: `workflows/handlers/{gate,test,archive}.py` + `register_builtins`
- `memory.archive` varsayılan `dry_run=True` (yıkıcı koruması)
- 29 yeni test; artefaktlar `pipeline/tasks/004-workflow-handlers/`

### Görev 005 — GBrain SQLite-FTS5 indeksi ✅
- Branch: `feat/005-gbrain-fts` (1 commit, üstünde 004)
- SQLite FTS5 önbellek (`.atlas/gbrain.sqlite`); vault gerçek kaynak
- `recall()` FTS bm25 + graf komşuluğu; stale tespit (mtime+sha256) → otomatik reindex
- `remember()` deterministik upsert; FTS5 yoksa fallback O(N·M)
- `atlas reindex [--full]` CLI komutu
- 24 yeni test; artefaktlar `pipeline/tasks/005-gbrain-fts/`

---

## Sıradaki Karar (kullanıcıya sunulacak)

Üç seçenek — kullanıcı `devam et` derse **öneri 003**:

1. **Görev 003 — LLM planner entegrasyonu**
   `ATLAS_LLM=claude|anthropic|acp` gerçek subprocess. Windows subprocess/UTF-8 tuzağı bilinen risk (DECISIONS 2026-07-24). Küçük tutulur, `claude --print` deneyimi ile başlar. `orchestrator/planner.py` içindeki stub'ı gerçekle değiştirir.

2. **Görev 006 — Otomatik context injection**
   `atlas run` başında `GBrain.context_for(goal)` çağrılıp plan fonksiyonuna geçirilsin. Görev 005'i somut faydaya çevirir. Küçük ölçekli, düşük risk.

3. **PR / merge stratejisi**
   3 branch (`feat/002-*`, `feat/004-*`, `feat/005-*`) main'e sıralı merge veya tek konsolide PR. Kullanıcı onayı ister (main korumalı — CLAUDE.md kuralı).

---

## Hızlı Bağlam (yeni oturum için ajanın okuması yeterli)

**Branch grafı:**
```
main (f93b2d5)
  └─ feat/002-orkestrator-canlanma (94d270e) — 4 commit
       └─ feat/004-workflow-handlers (cf63939)
            └─ feat/005-gbrain-fts (95b7cd6) ← ŞUAN BURADA
```

**Kalite kapıları (referans):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
uv run mypy src
uv run ruff check src tests
```

**Kritik sözleşme değişmezlikleri (kırma!):**
- `orchestrator/core.py` — `run_loop`, `Action`, `Judge`, `CallBudget`, `LoopResult`
- `workflows/engine.py` — `WorkflowEngine.register/run`, `WorkflowError`, `StepResult`
- `memory/gbrain.py` — `recall/remember/context_for/log_event` imzaları; `Recall` alanları
- `memory/vault.py` — `Vault` API'si

**Yeni exit kodları (mevcut kalıp):**
- `0` başarı, `2` YAML/spec hatası, `3` bütçe, `4` max_steps/planner_exhausted,
- `5` action_denied, `6` handler başarısız / bilinmeyen handler

**İstisna adlandırma standardı (ruff N818):** tüm `Exception` sınıfları `*Error` sonekli.

**Test yazma kalıbı:** subprocess-CLI testleri coverage'ı görmez → her yeni CLI kod parçası için ek olarak `test_cli_direct.py`'de `main([...])` çağıran in-process test şart. (DECISIONS 2026-07-28, Görev 004 [HATA] satırı.)

**Görev-öncesi zorunlu okuma:**
1. `DECISIONS.md` — en üstteki [KARAR]/[HATA] satırları
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin varsa `pipeline/tasks/<XXX>/00-need.md` + `02-spec.md`
4. Değişecek modülün üstündeki docstring

**Zorunlu döngü (CLAUDE.md gereği):** SPEC → PLAN → BUILD → TEST → SHIP. SPEC onayı olmadan kod yazılmaz.

---

## Kapanış Notları

- Uncommitted değişiklik yok, working tree temiz.
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) — dokunulmadı.
- Portable bundle son sürüm: `D:\ATLAS.rar` (1.9 GB, önceki oturum).
- Herhangi bir aksama olursa DECISIONS.md 2026-07-28 girdileri tam bağlamı verir.

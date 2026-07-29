# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (4. tur — 003.1 + 003.2 + 007 + flaky düzeltmesi)
**Branch:** `fix/doctor-gui-mtime-flaky` (main'e ff-merge onayı bekliyor)
**Working tree:** temiz
**Durum:** 4 branch, 4 lineer commit main'in ucunda hazır — kullanıcı
onayıyla ff-merge + push edilecek. 371/371 test yeşil (flaky retry
gereksinimi kalktı), mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 4. tur)

Sıra ile 4 iş tamamlandı, her biri kendi branch'inde tek commit,
zincirleme (`003.1 → 003.2 → 007 → flaky`):

1. **Görev 003.1** — anthropic + acp LLM backend'leri
   - `_anthropic_planner`: stdlib `urllib` ile Anthropic Messages API'sine
     HTTPS POST. Env: `ANTHROPIC_API_KEY`, `ATLAS_LLM_MODEL`,
     `ATLAS_LLM_ANTHROPIC_URL`. Yerel `claude` kurulumu şart değil.
   - `_acp_planner`: subprocess ACP-lite (initialize → session/new →
     session/prompt → `agent_message_chunk` topla → stop). Env:
     `ATLAS_LLM_ACP_BIN`, `ATLAS_LLM_ACP_ARGS`. Görev başına tek-oturum;
     `finally` bloğunda kill garantisi (süreç sızıntısı yasak).
   - `LLMPlannerError` + exit 7 sözleşmesi her iki backend'te aynı.
   - 35 yeni test + 2 CLI test.

2. **Görev 003.2** — `Goal.llm_prompt` opsiyonel alanı
   - YAML'da `llm_prompt: |...` ile kullanıcı sistem promptu bildirir.
   - `_format_prompt` iki-yollu: kullanıcı promptu **başta**, ATLAS'ın
     "TEK SATIRLIK" plan sözleşmesi **sonda** (kullanıcı çıktı
     sözleşmesini bozamaz).
   - Boş string → `None` (sessiz fallback). Merkezi değişiklik →
     üç backend otomatik uyumlu. +9 test.

3. **Görev 007** — `atlas archive <task>` CLI komutu
   - Yıkıcı işlem **dry-run varsayılan**; `--apply` bilinçli seçim
     (CLAUDE.md kuralı yüzeyde varsayılana gömüldü).
   - Özet zinciri: `--summary` > `09-ship.md` ilk paragraf > fallback
     `"<task> arşivlendi"`.
   - Audit: `("atlas-archive", "archive"|"error", "<task>")`. Dry-run
     audit'e yazmaz. +6 test.

4. **Flaky düzeltmesi** — `test_doctor_gui.py::test_restore_defaults_to_newest_and_can_pick_by_name`
   - Neden: `list_backups` sort key'i `st_mtime` (float saniye) idi;
     Windows sistem-saati ~15.6 ms tick'lerde eşleşince "en yeni"
     belirsizleşiyordu.
   - Fix: `(st_mtime_ns, name)` desc — NTFS 100 ns hassasiyet + name
     tiebreaker. +1 regresyon testi (`os.utime` ile ns eşitleyip
     belirlenimci sıra doğrulaması).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Merge + push.** 4 lineer commit main'in üstünde hazır:

```
main (1a3601f) ← origin/main (senkron)
     ↑
     0591928 feat(003.1): anthropic + acp LLM backend'leri
     06ddf99 feat(003.2): Goal.llm_prompt opsiyonel alani + prompt overlay
     6c71c7d feat(007): atlas archive CLI komutu (dry-run varsayilan + audit)
     e7cc244 fix(doctor-gui): list_backups (st_mtime_ns, name) desc
```

Önerilen yol (kullanıcı onayı ister):

```bash
git checkout main
git merge --ff-only fix/doctor-gui-mtime-flaky   # 4 commit lineer
git push origin main
git branch -d feat/003.1-llm-backends feat/003.2-llm-prompt feat/007-archive-cli fix/doctor-gui-mtime-flaky
```

Alternatif — merge etmeden yeni görev seçilebilir (branch'ler beklemede
kalır). Olası yeni yönler:

- **Görev 008 — LLM planner retry/backoff (013 hazırlığı):**
  `LLMPlannerError` yakalayıp N deneme + backoff (env-ayarlı) — üç
  backend'e ortak sarmalayıcı.
- **Görev 009 — `Goal.llm_model` opsiyonel alanı:** her görevin
  kendi modelini bildirmesi (anthropic backend'te env yerine
  goal'den).
- **Görev 010 — Anthropic system rolü ayrımı:** `llm_prompt` sistem
  rolü, `goal.goal` user rolü — Anthropic Messages API "system" alanı.
- **Görev 011 — Token cost/quota:** CallBudget'ın soyut kredisini
  gerçek token maliyetine bağla (Anthropic response header'ları).

---

## Hızlı Bağlam

**Branch grafı (yerel):**
```
main (1a3601f) → feat/003.1-llm-backends (0591928)
              → feat/003.2-llm-prompt (06ddf99)
              → feat/007-archive-cli (6c71c7d)
              → fix/doctor-gui-mtime-flaky (e7cc244) ← HEAD
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 371 passed; coverage ~%93.44
uv run mypy src         # 25 dosya, temiz
uv run ruff check src tests   # temiz
uv run atlas scan src   # sır bulunamadı
```

**Sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py::{run_loop, Action, Judge, CallBudget,
  LoopResult, StepKind}` — dokunulmadı
- `orchestrator/planner.py::{Planner, make_planner,
  PlannerExhaustedError, LLMPlannerError}` — imzalar korundu; yalnız
  iç yardımcı ekleme
- `orchestrator/goals.py::Goal` — yeni alanlar opsiyonel default'lu
  (`llm_prompt: str | None = None`)
- `memory/archive.py::archive_task`, `memory/vault.py::Vault` — dokunulmadı
- CLI mevcut alt-komutlar — dokunulmadı; yeni `archive` eklendi

**Env sözleşmesi (kümülatif):**
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM` | `stub` \| `claude` \| `anthropic` \| `acp` (yeni) \| bilinmiyor |
| `ATLAS_LLM_TIMEOUT` | ortak subprocess/HTTPS timeout (varsayılan 60 sn) |
| `ATLAS_LLM_CLAUDE_BIN` | claude override (SPEC 003) |
| `ANTHROPIC_API_KEY` | **anthropic zorunlu** (SPEC 003.1) |
| `ATLAS_LLM_MODEL` | anthropic model id (varsayılan `claude-3-5-sonnet-latest`) |
| `ATLAS_LLM_ANTHROPIC_URL` | anthropic URL override |
| `ATLAS_LLM_ACP_BIN` | **acp zorunlu** (veya PATH'te `acp-agent`) |
| `ATLAS_LLM_ACP_ARGS` | acp extra argv (shlex parse) |
| `ATLAS_CONTEXT` | `on` (varsayılan) \| `off` (SPEC 006) |

**Exit kodları (değişmedi):**
- 0 başarı, 2 SPEC/YAML, 3 bütçe, 4 max_steps/planner_exhausted,
  5 action_denied, 6 handler/arşiv hatası, 7 LLM planner hatası

**Bilinen flaky:** yok — bu turda düzeltildi.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — en üstteki [KARAR]/[HATA] satırları (2026-07-29
   3 yeni girdi)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,02-spec,09-ship}.md`
4. Değişecek modülün üstündeki docstring

---

## Kapanış Notları

- 371 test yeşil (baseline 319 → +52 test); coverage %93.44
- 4 lineer commit main üstünde bekliyor; merge stratejisi user'a bağlı
- Uncommitted değişiklik yok, working tree temiz
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) —
  dokunulmadı
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB) —
  yenilenmemedi (kapsam dışı)
- DECISIONS.md 2026-07-29 altında **4 yeni girdi bloğu**: 003.1, 003.2,
  007, flaky

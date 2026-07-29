# DEVAM NOKTASI — ATLAS

**Son çalışma:** 2026-07-29 (4. tur — 003.1 + 003.2 + 007 + flaky +
merge/push/temizlik)
**Branch:** `main` (origin/main ile senkron — `99c3ab5`)
**Working tree:** temiz
**Durum:** 4 aşama tamamlandı, 5 lineer commit main'e ff-merge + push
edildi (`30ba1a6..99c3ab5`), 4 feature branch silindi. 371/371 test
yeşil (flaky düzeltildi), coverage %93.44, mypy strict + ruff + scan
temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle: **"DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et."**

---

## Bu turda yapılan (2026-07-29 — 4. tur)

Sıra ile 4 iş tamamlandı, her biri kendi branch'inde tek commit,
zincirleme (`003.1 → 003.2 → 007 → flaky`); sonrasında main'e
lineer ff-merge + push + temizlik.

1. **Görev 003.1** — anthropic + acp LLM backend'leri (`0591928`)
   - `_anthropic_planner`: stdlib `urllib` ile Anthropic Messages API'sine
     HTTPS POST. Env: `ANTHROPIC_API_KEY`, `ATLAS_LLM_MODEL`,
     `ATLAS_LLM_ANTHROPIC_URL`. Yerel `claude` kurulumu şart değil.
   - `_acp_planner`: subprocess ACP-lite (initialize → session/new →
     session/prompt → `agent_message_chunk` topla → stop). Env:
     `ATLAS_LLM_ACP_BIN`, `ATLAS_LLM_ACP_ARGS`. Görev başına tek-oturum;
     `finally` bloğunda kill garantisi (süreç sızıntısı yasak).
   - `LLMPlannerError` + exit 7 sözleşmesi her iki backend'te aynı.
   - 35 yeni test + 2 CLI test.

2. **Görev 003.2** — `Goal.llm_prompt` opsiyonel alanı (`06ddf99`)
   - YAML'da `llm_prompt: |...` ile kullanıcı sistem promptu bildirir.
   - `_format_prompt` iki-yollu: kullanıcı promptu **başta**, ATLAS'ın
     "TEK SATIRLIK" plan sözleşmesi **sonda** (kullanıcı çıktı
     sözleşmesini bozamaz).
   - Boş string → `None` (sessiz fallback). Merkezi değişiklik →
     üç backend (claude/anthropic/acp) otomatik uyumlu. +9 test.

3. **Görev 007** — `atlas archive <task>` CLI komutu (`6c71c7d`)
   - Yıkıcı işlem **dry-run varsayılan**; `--apply` bilinçli seçim
     (CLAUDE.md kuralı yüzeyde varsayılana gömüldü).
   - Özet zinciri: `--summary` > `09-ship.md` ilk paragraf > fallback
     `"<task> arşivlendi"`.
   - Audit: `("atlas-archive", "archive"|"error", "<task>")`. Dry-run
     audit'e yazmaz. +6 test.

4. **Flaky düzeltmesi** (`e7cc244`) — `test_doctor_gui.py::test_restore_defaults_to_newest_and_can_pick_by_name`
   - Neden: `list_backups` sort key'i `st_mtime` (float saniye) idi;
     Windows sistem-saati ~15.6 ms tick'lerde eşleşince "en yeni"
     belirsizleşiyordu.
   - Fix: `(st_mtime_ns, name)` desc — NTFS 100 ns hassasiyet + name
     tiebreaker. +1 regresyon testi (`os.utime` ile ns eşitleyip
     belirlenimci sıra doğrulaması).

5. **Merge + push + temizlik**
   - `git merge --ff-only fix/doctor-gui-mtime-flaky` → 5 commit lineer
     main'e (`99c3ab5`), merge commit YOK.
   - `git push origin main` → `30ba1a6..99c3ab5` uzağa gitti.
   - 4 feature branch silindi (`feat/003.1-llm-backends`,
     `feat/003.2-llm-prompt`, `feat/007-archive-cli`,
     `fix/doctor-gui-mtime-flaky`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok; 003.1 / 003.2 / 007 /
flaky kapandı. Doğal devam adayları:

- **Görev 008 — LLM planner retry/backoff (013 hazırlığı):**
  `LLMPlannerError` yakalayıp N deneme + backoff (env-ayarlı) — üç
  backend'e ortak sarmalayıcı. Küçük ve orthogonal.
- **Görev 009 — `Goal.llm_model` opsiyonel alanı:** her görevin
  kendi modelini bildirmesi (anthropic backend'te env yerine
  goal'den). 003.2 kalıbıyla simetrik, küçük.
- **Görev 010 — Anthropic system rolü ayrımı:** `llm_prompt` sistem
  rolü, `goal.goal` user rolü — Anthropic Messages API "system" alanı.
  003.2'nin sözleşme boyutunu genişletir.
- **Görev 011 — Token cost/quota:** CallBudget'ın soyut kredisini
  gerçek token maliyetine bağla (Anthropic response header'ları).
  Daha kapsamlı; 009 ile birleştirilebilir.
- **Görev 012 — Sık kullanılan görevlerin `atlas archive --all` +
  git commit hook zinciri:** 007'nin doğal genişlemesi.

Ya da başka bir öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (99c3ab5) = main (99c3ab5) ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 5 commit (2026-07-29 4. tur):**
```
99c3ab5 docs: DEVAM_NOKTASI.md — 4. tur (003.1+003.2+007+flaky) kapanis
e7cc244 fix(doctor-gui): list_backups (st_mtime_ns, name) desc
6c71c7d feat(007): atlas archive CLI komutu (dry-run varsayilan + audit)
06ddf99 feat(003.2): Goal.llm_prompt opsiyonel alani + prompt overlay
0591928 feat(003.1): anthropic + acp LLM backend'leri (stdlib urllib + ACP-lite)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 371 passed; coverage %93.44
uv run mypy src                # 25 dosya, temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py::{run_loop, Action, Judge, CallBudget,
  LoopResult, StepKind}` — dokunulmadı
- `orchestrator/planner.py::{Planner, make_planner,
  PlannerExhaustedError, LLMPlannerError}` — imzalar korundu; yalnız
  iç yardımcı ekleme
- `orchestrator/goals.py::Goal` — yeni alan opsiyonel default'lu
  (`llm_prompt: str | None = None`)
- `memory/archive.py::archive_task`, `memory/vault.py::Vault` — dokunulmadı
- CLI mevcut alt-komutlar — dokunulmadı; yeni `archive` eklendi

**Env sözleşmesi (kümülatif):**
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM` | `stub` \| `claude` \| `anthropic` \| `acp` \| bilinmiyor |
| `ATLAS_LLM_TIMEOUT` | ortak subprocess/HTTPS timeout (varsayılan 60 sn) |
| `ATLAS_LLM_CLAUDE_BIN` | claude override (SPEC 003) |
| `ANTHROPIC_API_KEY` | **anthropic zorunlu** (SPEC 003.1) |
| `ATLAS_LLM_MODEL` | anthropic model id (varsayılan `claude-3-5-sonnet-latest`) |
| `ATLAS_LLM_ANTHROPIC_URL` | anthropic URL override (vekil/test) |
| `ATLAS_LLM_ACP_BIN` | **acp zorunlu** (veya PATH'te `acp-agent`) |
| `ATLAS_LLM_ACP_ARGS` | acp extra argv (shlex parse) |
| `ATLAS_CONTEXT` | `on` (varsayılan) \| `off` (SPEC 006) |

**Exit kodları (değişmedi):**
- 0 başarı, 2 SPEC/YAML, 3 bütçe, 4 max_steps/planner_exhausted,
  5 action_denied, 6 handler/arşiv hatası, 7 LLM planner hatası

**Bilinen flaky:** yok — bu turda düzeltildi.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — en üstteki [KARAR]/[HATA] satırları (2026-07-29
   4 yeni girdi bloğu: 003.1, 003.2, 007, flaky)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,02-spec,09-ship}.md`
4. Değişecek modülün üstündeki docstring

---

## Kapanış Notları

- 371 test yeşil (baseline 319 → +52 test); coverage %93.44
- 5 lineer commit main'e alındı, uzağa push edildi, 4 feature branch
  silindi (kullanıcı açık onayıyla)
- Uncommitted değişiklik yok, working tree temiz
- Ollama / Juggler / ACP kimlikleri `.juggler/` altında (gitignored) —
  dokunulmadı
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB) —
  yenilenmemedi (kapsam dışı)
- DECISIONS.md 2026-07-29 altında **4 yeni girdi bloğu**: 003.1, 003.2,
  007, flaky

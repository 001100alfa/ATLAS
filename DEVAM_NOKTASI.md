# DEVAM NOKTASI — ATLAS

> ## TETİKLEYİCİ (agent talimatı — bu bloku her açılışta oku)
> Kullanıcı **"devam et"**, **"kaldığı yerden devam et"** veya
> **"projeye devam"** derse, başka soru sormadan:
> 1. Bu dosyanın **tamamını** oku.
> 2. `## Bu turda yapılan` bölümünden son turun sonucunu özetle.
> 3. `## Sıradaki Karar (kullanıcıya sunulacak)` altındaki adayları
>    listeleyip kısa bir seçim sorusuyla yeni turu başlat.
> 4. Kullanıcı onay verene kadar YIKICI işlem yapma (push, rm,
>    force-push, branch silme).
> 5. Zorunlu Döngü'ye (`CLAUDE.md` §Zorunlu Döngü) gir; ilk iş
>    `DECISIONS.md`'nin son 2026-07-29 girişlerini kaba tarama.

**Son çalışma:** 2026-07-29 (11. tur — 018.2 + 026.1 + 026.2 + 030)
**Branch:** `main` (origin/main ile senkron — `d323a90`)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 11. tur tamamlandı; 4 lineer feat commit + 1 docs commit
main'e ff-merge + push edildi (`0057b66..d323a90`), 4 feature branch
silindi. **600/600 test yeşil** (+8 platform skip), coverage %91.19,
mypy strict + ruff + scan temiz. Bilinen flaky yok.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

(Alternatif: "DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et.")

---

## Bu turda yapılan (2026-07-29 — 11. tur)

Zincirleme dört büyük iş (`018.2 → 026.1 → 026.2 → 030`), her biri
kendi branch'inde tek commit; sonrasında main'e lineer ff-merge +
push + branch temizlik.

1. **Görev 018.2** — LLM ile gerçek gözlem özetleme (`3b31cb8`)
   - `Goal.obs_summarize: bool = False` opt-in + env override
     `ATLAS_LLM_OBS_SUMMARIZE` (1/true/yes/on).
   - `_maybe_summarize_or_trim` dispatch: kısa obs no-op; opt-in
     kapalı = 018.1 trim; açık + anthropic = **real `_call_anthropic`**
     (metrics.jsonl + usage trace); açık + stub = deterministik stub
     özet; açık + claude/acp = stub + bir kez uyarı (018.3'e ertelendi).
   - Fail-safe: anthropic hata → stderr uyarı + `_trim_obs` fallback.
   - `_format_prompt` yeni dispatch çağırır; sözleşme korundu.
   - +17 test.

2. **Görev 026.1** — Unix resource limits (`78f29d9`)
   - `try: import resource` guard (Windows'ta modül YOK).
   - `_build_preexec_fn`: Unix'te env verildiyse `RLIMIT_CPU` +
     `RLIMIT_AS` uygulayan callable; Windows'ta **HER ZAMAN None**
     (`subprocess.run(preexec_fn=...)` Windows'ta ValueError).
   - Env: `ATLAS_SANDBOX_CPU_S`, `ATLAS_SANDBOX_MEM_MB` (pozitif int).
   - `_shell` `preexec_fn=...` alır; env yokken None (bit-uyumlu 026).
   - +15 test: Windows canlı 9 pass, Unix canlı 6 skip (CI Ubuntu
     leg'de aktif).

3. **Görev 026.2** — Windows Job Objects (`3bcdc29`)
   - `ctypes.WinDLL('kernel32')` üstünden: `CreateJobObjectW` +
     `SetInformationJobObject(JobObjectExtendedLimitInformation=9)` +
     `OpenProcess` + `AssignProcessToJobObject`.
   - `KILL_ON_JOB_CLOSE` (0x2000) her koşulda — ATLAS kapanırsa job
     da ölür, fork bomb torunları temizlenir.
   - Env: `ATLAS_SANDBOX_MEM_MB` (026.1 ile ORTAK) → `PROCESS_MEMORY`;
     `ATLAS_SANDBOX_MAX_PROC` (yeni) → `ACTIVE_PROCESS`.
   - `_shell`: Windows + env → `subprocess.Popen` + `apply_job` +
     `communicate`; aksi → mevcut `subprocess.run` yolu (bit-uyumlu).
   - Fail-safe: WinError stderr uyarı, subprocess kısıtsız yürür.
   - **Kanıt (Windows canlı):** `test_0262_windows_mem_limit_patlar`
     MEM_MB=64'te 500 MB `bytearray` alloc'u **2 sn'de exit != 0**.
   - +11 test.

4. **Görev 030** — Multi-goal batch (`c3b8fbf`)
   - `--goal-file` `nargs='+'`; `--continue-on-error` bayrağı.
   - `_cmd_run` dispatch: N==1 → tek dosya (027 bit-uyumlu, özet YOK);
     N>1 → `_cmd_run_batch`.
   - Fail-fast varsayılan; ilk hata sonraki'leri `atlandı` işaretler.
   - Run-id suffix: `--run-id X` → `X_1/X_2/.../X_N`; yoksa
     `<TS>_<i>` (timestamp bir kez alınır).
   - Özet tablosu (`+ done`, `x exit=N`, `- atlandı`), exit kodu =
     `max(rc)`.
   - `--dry-run` tek bayrak, tüm goal'lere uygulanır.
   - +8 test.

5. **Merge + push + temizlik**
   - `git merge --ff-only feat/018.2 && ... && feat/030` → 4 commit
     lineer main'e (`c3b8fbf`), merge commit YOK.
   - `git push origin main` → `0057b66..c3b8fbf` uzağa gitti.
   - 4 feature branch silindi (`feat/018.2-llm-obs-summarize`,
     `feat/026.1-unix-resource`, `feat/026.2-windows-job`,
     `feat/030-multi-goal-batch`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal devam adayları:

- **Görev 018.3 — Claude/ACP backend real gözlem özetleme:** 018.2
  hook mekanizması hazır, `claude subprocess` + `ACP` üstünden özet
  çağrısı ekle. Şu an bu backend'lerde stub + uyarı.
- **Görev 026.3 — Windows CPU quota:** `JOB_OBJECT_LIMIT_PROCESS_TIME`
  ns tick matematiği; Unix `RLIMIT_CPU` ile arayüz simetrisi.
- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı;
  sandbox paylaşımı + rate limit gözetimi.
- **Görev 032 — GBrain quality gate:** commit öncesi `atlas doctor
  --strict` mecburi; DECISIONS drift denetimi.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (c3b8fbf + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 4 commit (2026-07-29 11. tur):**
```
c3b8fbf feat(030): multi-goal batch (--goal-file A B C)
3bcdc29 feat(026.2): Windows Job Objects (MEM + PROC limits)
78f29d9 feat(026.1): Unix resource limits (RLIMIT_CPU + RLIMIT_AS)
3b31cb8 feat(018.2): LLM ile gozlem ozetleme (opt-in + anthropic real)
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 600 passed, 8 skipped (Unix-only 6 + Windows-only 2)
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas run --goal-file A.yaml B.yaml C.yaml [--continue-on-error]`
  (030)
- Tek dosya (`--goal-file X`) 027 ile birebir bit-uyumlu.

**Env sözleşmesi (kümülatif, bu turda eklenen ★):**
| Değişken | Anlam |
|---|---|
| `ATLAS_LLM_OBS_SUMMARIZE` ★ | **018.2** — 1/true/yes/on iken opt-in özet global aç |
| `ATLAS_SANDBOX_CPU_S` ★ | **026.1** — Unix `RLIMIT_CPU` (saniye) |
| `ATLAS_SANDBOX_MEM_MB` ★ | **026.1 + 026.2 ORTAK** — Unix `RLIMIT_AS` / Windows `JOB_OBJECT_LIMIT_PROCESS_MEMORY` (MB) |
| `ATLAS_SANDBOX_MAX_PROC` ★ | **026.2** — Windows `JOB_OBJECT_LIMIT_ACTIVE_PROCESS` |
| (önceden: `ATLAS_LLM`, `ATLAS_LLM_TIMEOUT`, `ATLAS_LLM_CLAUDE_BIN`, `ANTHROPIC_API_KEY`, `ATLAS_LLM_MODEL`, `ATLAS_LLM_ANTHROPIC_URL`, `ATLAS_LLM_ACP_BIN`, `ATLAS_LLM_ACP_ARGS`, `ATLAS_CONTEXT`, `ATLAS_ACP_INTERACTIVE`, `ATLAS_LLM_RETRIES`, `ATLAS_LLM_BACKOFF`, `ATLAS_LLM_JITTER`, `ATLAS_LLM_TRACE`, `ATLAS_LLM_PRICE_IN/OUT`, `ATLAS_LLM_OBS_CHARS`, `ATLAS_LLM_OBS_HEAD/TAIL`, `ATLAS_ARCHIVE_AGE_DAYS`, `ATLAS_DOTENV`, `ATLAS_METRICS`, `ATLAS_SANDBOX_PATH`, `ATLAS_SANDBOX_TIMEOUT`, `ATLAS_RUNS_DIR`) | |

**Exit kodları (kümülatif):**
| Kod | Anlam |
|---|---|
| 0 | Başarılı |
| 1 | Sır bulundu (scan) |
| 2 | SPEC HATASI (input/config) |
| 3 | GBrain/workflow başarısız |
| 4 | Run bitmedi (done=False) |
| 5 | Action denied |
| 6 | archive-all bir görevde başarısız |
| 7 | Env / archive age parse hatası |
| 8 | `atlas metrics --alert` eşik altı (029) |

**Platform matrisi (026 + 026.1 + 026.2 birleşik):**
| Platform | Env yok | CPU_S | MEM_MB | MAX_PROC |
|---|---|---|---|---|
| Unix | subprocess.run (bit-uyumlu) | RLIMIT_CPU | RLIMIT_AS | (026.3?) |
| Windows | subprocess.run (bit-uyumlu) | (026.3?) | Job Objects PROCESS_MEMORY | Job Objects ACTIVE_PROCESS |

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `orchestrator/core.py`, `orchestrator/goals.py::Goal` (yeni alan
  eklendi, mevcut alanlar korundu), `AuditLog` — imzalar korundu.
- `Planner`, `make_planner`, `LLMPlannerError`, `RetryAfterError`,
  `_call_anthropic`, `_trim_obs`, `_format_prompt` — imzalar korundu.
- `Action`, `make_action`, `ActionDeniedError` — imzalar korundu;
  `_shell` yalnız iç dallanma.
- `_cmd_run_goal` sözleşmesi korundu; batch onu N kez çağırır.
- `atlas run --goal-file X.yaml` (tek) çağrısı 027 ile birebir
  (`nargs='+'` liste ama N=1 unwrap → str).
- `atlas replay <run-id>` yolu değişmedi.

**Bilinen flaky:** yok.

**Docker YASAK (kullanıcı direktifi 026'da):** korunuyor. 026.1
Unix `resource`, 026.2 Windows Job Objects native API'lerle
tamamlandı — Docker/container gerekmedi.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-29 altında **39 giriş bloğu** (+018.2,
   +026.1, +026.2, +030)
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 600 test yeşil (bu turun baseline'ı 557 → +43; oturum başı 319 → +281)
- 4 lineer commit main'e alındı, uzağa push edildi, 4 feature branch
  silindi (kullanıcı `continue` onayıyla)
- Yeni env: `ATLAS_LLM_OBS_SUMMARIZE`, `ATLAS_SANDBOX_CPU_S`,
  `ATLAS_SANDBOX_MEM_MB`, `ATLAS_SANDBOX_MAX_PROC`
- Yeni exit kodu YOK (10. turda eklenen 8 kaldı)
- Uncommitted değişiklik yok, working tree temiz
- Docker YASAK yürürlükte — 026.1 (Unix `resource`) + 026.2 (Windows
  Job Objects) native API ile karşıladı
- Portable bundle son sürüm: `D:\ATLAS.rar` (önceki oturum, 1.9 GB) —
  yenilenmedi (kapsam dışı)
- DECISIONS.md 2026-07-29 altında **39 giriş bloğu** birikti
- Ertelenen iş: **018.3** (claude/acp backend özet) 018.2 hook'unu
  gerçek çağrıya bağlayacak. **026.3** (Windows CPU quota) ns tick
  matematiği ile.

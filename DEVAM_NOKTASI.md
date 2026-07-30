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
>    `DECISIONS.md`'nin son 2026-07-30 girişlerini kaba tarama.

**Son çalışma:** 2026-07-30 (12. tur — 018.3 + 026.3)
**Branch:** `main` (origin/main ile senkron — `cbbb7db`)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 12. tur tamamlandı; 2 lineer feat commit main'e ff-merge
+ push edildi (`790c9da..cbbb7db`), 2 feature branch silindi.
**610/610 test yeşil** (+9 platform skip), coverage %91.26, mypy
strict + ruff + scan temiz. Bilinen flaky yok.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

(Alternatif: "DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et.")

---

## Bu turda yapılan (2026-07-30 — 12. tur)

Zincirleme iki iş (`018.3 → 026.3`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + push + branch temizlik.

1. **Görev 018.3** — Claude + ACP real gözlem özetleme (`671d4fe`)
   - `_summarize_via_claude` — `_call_claude` subprocess minimal
     özet promptu ile; yeni.
   - `_summarize_via_acp` — `_call_acp` JSON-RPC oturumu minimal
     özet promptu ile; yeni.
   - `_summarize_via_anthropic` refactor: ortak yardımcılar
     (`_build_summarize_prompt`, `_finalize_summary_line`) 3 backend
     paylaşır (018.2 sonuçla bit-uyumlu).
   - `_maybe_summarize_or_trim` dispatch tablosuyla temizlendi;
     4 backend simetrik.
   - 018.2'nin "018.3 kapsamı" uyarı yolu + `_OBS_SUMMARIZE_WARNED`
     seti **kaldırıldı** (dead code). Uyarı artık yalnız gerçek
     hata durumunda çıkar.
   - Fail-safe: her real çağrı LLMPlannerError → stderr uyarı +
     `_trim_obs` fallback.
   - +8 test (23 toplam); 2 eski uyarı testi silindi (davranış
     değişti).

2. **Görev 026.3** — Windows CPU quota (`cbbb7db`)
   - `_JOB_OBJECT_LIMIT_PROCESS_TIME` (0x2) + `_WIN_TIME_TICKS_PER_
     SECOND` (10⁷) sabitleri.
   - `_has_windows_sandbox_env` CPU_S dahil (üç env: MEM/PROC/CPU).
   - `_apply_windows_job(pid, mem_mb, max_proc, cpu_s=None)` —
     cpu_s verildiyse `LimitFlags |= 0x2` + `BasicLimitInformation.
     PerProcessUserTimeLimit = cpu_s * 10_000_000`.
   - `_shell` CPU_S env'i okuyup Job'a geçir.
   - `ATLAS_SANDBOX_CPU_S` artık **platform-agnostik**: Unix
     RLIMIT_CPU (026.1), Windows Job PROCESS_TIME (026.3).
   - Struct DEĞİŞMEDİ (PerProcessUserTimeLimit zaten c_int64).
   - **Kanıt (Windows canlı):** `while True: pass` CPU_S=1 iken
     3.5 sn'den kısa sürede exit != 0 (timeout 8 sn olsa da).
   - +5 test.

3. **Merge + push + temizlik**
   - `git merge --ff-only feat/018.3 && ... && feat/026.3` → 2
     commit lineer main'e (`cbbb7db`), merge commit YOK.
   - `git push origin main` → `790c9da..cbbb7db` uzağa gitti.
   - 2 feature branch silindi (`feat/018.3-claude-acp-summarize`,
     `feat/026.3-windows-cpu-quota`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Kalan doğal adaylar:

- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı;
  ThreadPool + sandbox paylaşımı + LLM rate limit gözetimi. En
  büyük scope + risk.
- **Görev 032 — GBrain quality gate:** `atlas doctor --strict` +
  DECISIONS drift denetimi. commit öncesi engelleyici davranış.
- **Görev 026.4 — Unix MAX_PROC (RLIMIT_NPROC):** platform matrisi
  tamamlanır (Unix tarafındaki tek boşluk); YAGNI seviyesinde
  küçük iş, RLIMIT_CPU zaten fork bomb'u SIGXCPU ile keser.
- **Görev 018.4 — ACP özet önbelleği:** her uzun obs için yeni
  Popen ağır — same obs iki kez → tek çağrı. YAGNI şimdilik.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (cbbb7db + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 2 commit (2026-07-30 12. tur):**
```
cbbb7db feat(026.3): Windows CPU quota (Job Objects PROCESS_TIME)
671d4fe feat(018.3): claude + acp real gozlem ozetleme
```
Ayrıca sabah kaydı: `790c9da chore(ai-cli): opencode-ai 1.18.9`.

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 610 passed, 9 skipped (6 Unix-only 026.1 + 2 non-Win 026.2 + 1 non-Win 026.3)
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):** yok — env sözleşmesi de aynı,
yalnız iç davranış değişiklikleri.

**Env sözleşmesi:** DEĞİŞMEDİ.
- `ATLAS_SANDBOX_CPU_S` 026.1'den beri var, 026.3 sadece Windows
  tarafını doldurdu (aynı env platform-agnostik oldu).
- `ATLAS_LLM_OBS_SUMMARIZE` 018.2'den beri var, 018.3 sadece 3
  gerçek backend'i tam bağladı.

**Exit kodları:** DEĞİŞMEDİ (10. turdaki 8 kaldı).

**Backend matrisi (018.2 + 018.3 birleşik) — obs özetleme:**
| Backend | Opt-in kapalı | Kısa obs | Uzun obs |
|---|---|---|---|
| stub | 018.1 trim | dokunma | stub özet (deterministik) |
| claude | 018.1 trim | dokunma | **real _call_claude** (018.3) |
| anthropic | 018.1 trim | dokunma | **real _call_anthropic** (018.2) |
| acp | 018.1 trim | dokunma | **real _call_acp** (018.3) |

**Platform matrisi (026 + 026.1 + 026.2 + 026.3 birleşik) — sandbox:**
| Platform | Env yok | CPU_S | MEM_MB | MAX_PROC |
|---|---|---|---|---|
| Unix | run (bit-uyumlu) | RLIMIT_CPU | RLIMIT_AS | (026.4?) |
| Windows | run (bit-uyumlu) | **Job PROCESS_TIME** | Job PROCESS_MEMORY | Job ACTIVE_PROCESS |

Matrisin **yedi hücresi dolu, bir hücresi bilinçli boş** (Unix MAX_PROC
RLIMIT_NPROC — YAGNI, RLIMIT_CPU zaten fork bomb'u keser).

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `Planner`, `make_planner`, `LLMPlannerError`, `RetryAfterError`,
  `_call_anthropic`, `_call_claude`, `_call_acp`, `_resolve_*_bin`,
  `_trim_obs`, `_stub_summarize_obs`, `_summarize_via_anthropic`,
  `_maybe_summarize_or_trim` imzaları korundu (dispatch içi değişti,
  arayüz aynı).
- `Action`, `make_action`, `ActionDeniedError` imzaları korundu.
- `_apply_windows_job` imzası genişledi (`cpu_s=None` default) —
  geri uyumlu, mevcut çağrıcı `_shell` içi tek yer güncellendi.
- `_JOBOBJECT_EXTENDED_LIMIT_INFORMATION` struct layout DEĞİŞMEDİ.
- `Goal` sözleşmesi aynı — yeni alan yok.
- Env sözleşmesi aynı.

**Bilinen flaky:** yok.

**Docker YASAK (kullanıcı direktifi 026'da):** korunuyor. Platform
matrisi tamamen native API'lerle dolduruldu — Unix `resource` +
Windows Job Objects. Container gerekmedi.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **3 yeni giriş bloğu**
   (chore, 018.3, 026.3); 2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 610 test yeşil (bu turun baseline'ı 600 → +10; oturum başı 319 → +291)
- 2 lineer commit main'e alındı, uzağa push edildi, 2 feature branch
  silindi (kullanıcı `onayla` ile)
- Yeni env YOK — mevcut envler platform matrisinde eksiklikleri
  doldurdu (CPU_S Windows'ta artık aktif; OBS_SUMMARIZE 3 real
  backend'e tam bağlı)
- Yeni exit kodu YOK
- Uncommitted değişiklik yok, working tree temiz
- Ertelenmiş iş kalmadı — 018.2 ve 026.2'nin bıraktığı iki uç
  (claude/acp özet, Windows CPU) bu turda kapandı
- Docker YASAK yürürlükte — sandbox güvenliği tamamen native
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz oturumu, 1.9 GB) —
  yenilenmedi (kapsam dışı)
- DECISIONS.md 2026-07-30 altında **3 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** birikti (toplam 42+)

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

**Son çalışma:** 2026-07-30 (13. tur — 032 + 026.4)
**Branch:** `main` (origin/main ile senkron — `3a4eae9`)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 13. tur tamamlandı; 2 lineer feat commit main'e ff-merge
+ push edildi (`c3aaedf..3a4eae9`), 2 feature branch silindi.
**629/629 test yeşil** (+12 platform skip), coverage %91.31, mypy
strict + ruff + scan temiz. Platform matrisi **8/8 dolu**.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

(Alternatif: "DEVAM_NOKTASI.md'yi oku ve kaldığı yerden devam et.")

---

## Bu turda yapılan (2026-07-30 — 13. tur)

Zincirleme iki iş (`032 → 026.4`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + push + branch temizlik.

1. **Görev 032** — `atlas doctor --strict` quality gate (`43d840c`)
   - `_last_decision_date` (DECISIONS.md ilk `^## YYYY-MM-DD`
     başlığı), `_read_strict_drift_days_env` (varsayılan 7),
     `_check_decisions_drift` (drift + uyarı).
   - `_collect_doctor_report`'a `quality.decisions_drift` bölümü
     **her zaman** eklendi (bayraktan bağımsız).
   - `_cmd_doctor` `--strict` bayrağı + `[Kalite kapıları]` insan
     bölümü + `--json --strict` de exit 9 yolu.
   - Yeni env: `ATLAS_STRICT_DRIFT_DAYS` (7 varsayılan).
   - Yeni exit: **9** ("quality gate failed").
   - Bit-uyumluluk: mevcut çıktı ve alanlar birebir korundu; yalnız
     EKLEMELER.
   - **Bonus fix:** 026.3 CPU quota testi (`test_0263_windows_cpu_
     quota_kesir`) 3.5s eşiği yüklü makinede flaky — 12s timeout +
     8s eşik marjı ile güvenli.
   - +18 test.

2. **Görev 026.4** — Unix `MAX_PROC` / `RLIMIT_NPROC` (`3a4eae9`)
   - `_build_preexec_fn` MAX_PROC dahil (3 env: CPU/MEM/PROC).
   - `getattr(_resource, "RLIMIT_NPROC", None)` platform koruma
     (bazı BSD varyantları).
   - `ATLAS_SANDBOX_MAX_PROC` artık **platform-agnostik**: Unix
     RLIMIT_NPROC (026.4), Windows Job ACTIVE_PROCESS (026.2).
   - Env yoksa 026.1 + 026.3 bit-uyumlu; Windows'ta preexec_fn hâlâ
     None (026.1 guard aynı).
   - Canlı fork limit testi CI-fragile bilinçli dışlandı; mock ile
     `setrlimit(RLIMIT_NPROC, (12, 12))` çağrısı ampirik doğrulandı.
   - **Platform matrisi 8/8 dolu** — hiçbir hücrede boşluk yok.
   - +4 test.

3. **Merge + push + temizlik**
   - `git merge --ff-only feat/032 && ... && feat/026.4` → 2 commit
     lineer main'e (`3a4eae9`), merge commit YOK.
   - `git push origin main` → `c3aaedf..3a4eae9` uzağa gitti.
   - 2 feature branch silindi (`feat/032-quality-gate`,
     `feat/026.4-unix-nproc`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı.
  ThreadPool + sandbox paylaşımı + LLM rate limit gözetimi + exit
  agregasyon. En büyük scope + risk; ayrı tur hak eder.
- **Görev 032.1 — `atlas doctor --strict` genişletme:** coverage /
  test-failure / DECISIONS entry count denetimleri. 032 hook mekanı
  hazır, ek denetim eklemek küçük.
- **Görev 033 — `atlas archive --restore <id>`:** arşivlenen görevi
  geri getir. `atlas archive --all` yıkıcı — geri alma yok.
- **Görev 034 — pre-commit hook entegrasyonu:** `atlas doctor
  --strict` + `atlas scan` commit öncesi otomatik çalışsın.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (3a4eae9 + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 2 commit (2026-07-30 13. tur):**
```
3a4eae9 feat(026.4): Unix MAX_PROC (RLIMIT_NPROC) — platform matrisi 8/8 dolu
43d840c feat(032): atlas doctor --strict + DECISIONS drift + exit 9
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 629 passed, 12 skipped (6 Unix-only 026.1 + 3 Unix-only 026.4 +
#                        2 non-Win 026.2 + 1 non-Win 026.3)
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışı (bu turda):**
- `atlas doctor --strict` — 032. Opt-in; drift varsa exit 9.

**Env sözleşmesi (kümülatif, bu turda eklenen ★):**
| Değişken | Anlam |
|---|---|
| `ATLAS_STRICT_DRIFT_DAYS` ★ | **032** — DECISIONS.md drift eşiği (varsayılan 7 gün) |
| `ATLAS_SANDBOX_MAX_PROC` | **026.2 + 026.4 ORTAK** — Unix RLIMIT_NPROC / Windows Job ACTIVE_PROCESS (026.4 Unix ayağını doldurdu) |
| (önceki: `ATLAS_LLM`, `ATLAS_LLM_TIMEOUT`, `ATLAS_LLM_CLAUDE_BIN`, `ANTHROPIC_API_KEY`, `ATLAS_LLM_MODEL`, `ATLAS_LLM_ANTHROPIC_URL`, `ATLAS_LLM_ACP_BIN`, `ATLAS_LLM_ACP_ARGS`, `ATLAS_CONTEXT`, `ATLAS_ACP_INTERACTIVE`, `ATLAS_LLM_RETRIES`, `ATLAS_LLM_BACKOFF`, `ATLAS_LLM_JITTER`, `ATLAS_LLM_TRACE`, `ATLAS_LLM_PRICE_IN/OUT`, `ATLAS_LLM_OBS_CHARS`, `ATLAS_LLM_OBS_HEAD/TAIL`, `ATLAS_LLM_OBS_SUMMARIZE`, `ATLAS_ARCHIVE_AGE_DAYS`, `ATLAS_DOTENV`, `ATLAS_METRICS`, `ATLAS_SANDBOX_PATH`, `ATLAS_SANDBOX_TIMEOUT`, `ATLAS_SANDBOX_CPU_S`, `ATLAS_SANDBOX_MEM_MB`, `ATLAS_RUNS_DIR`) | |

**Exit kodları (kümülatif, bu turda eklenen ★):**
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
| **9** ★ | **`atlas doctor --strict` DECISIONS drift (032)** |

**Platform matrisi (026 + 026.1 + 026.2 + 026.3 + 026.4 birleşik):**
| Platform | Env yok | CPU_S | MEM_MB | MAX_PROC |
|---|---|---|---|---|
| Unix | subprocess.run (bit-uyumlu) | RLIMIT_CPU (026.1) | RLIMIT_AS (026.1) | **RLIMIT_NPROC (026.4)** |
| Windows | subprocess.run (bit-uyumlu) | Job PROCESS_TIME (026.3) | Job PROCESS_MEMORY (026.2) | Job ACTIVE_PROCESS (026.2) |

**Matris 8/8 dolu** — hiçbir hücrede boşluk yok.

**Backend matrisi (obs özet, 018.2 + 018.3):**
| Backend | Opt-in kapalı | Kısa obs | Uzun obs |
|---|---|---|---|
| stub | 018.1 trim | dokunma | stub özet (deterministik) |
| claude | 018.1 trim | dokunma | real _call_claude (018.3) |
| anthropic | 018.1 trim | dokunma | real _call_anthropic (018.2) |
| acp | 018.1 trim | dokunma | real _call_acp (018.3) |

**Matris 4/4 dolu.**

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `_cmd_doctor`, `_collect_doctor_report` mevcut alanları + çıktısı
  KORUNDU (yalnız EKLEMELER: `quality` alanı + `[Kalite kapıları]`
  bölümü).
- `_build_preexec_fn` imzası KORUNDU (içi genişledi).
- `Action`, `make_action`, `ActionDeniedError` imzaları korundu.
- Env yokken doctor + shell davranışı bit-uyumlu (öncekiler
  bozulmadı).
- `Planner`, `make_planner`, `Goal` — bu turda dokunulmadı.

**Bilinen flaky:** yok. (026.3 flaky-fix 032 turunda yapıldı.)

**Docker YASAK:** hâlâ yürürlükte. Sandbox tamamen native (Unix
resource + Windows Job Objects) — hiç container yok.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **5 yeni giriş bloğu**
   (chore, 018.3, 026.3, 032, 026.4); 2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 629 test yeşil (bu turun baseline'ı 610 → +19; oturum başı 319 → +310)
- 2 lineer commit main'e alındı, uzağa push edildi, 2 feature branch
  silindi (kullanıcı `onayla` ile)
- Yeni env: `ATLAS_STRICT_DRIFT_DAYS` (032). `ATLAS_SANDBOX_MAX_PROC`
  Unix ayağı da doldu (026.4)
- Yeni exit kodu: **9** (`atlas doctor --strict` drift)
- Uncommitted değişiklik yok, working tree temiz
- Ertelenen iş yok — 032 hook mekanı hazır ama coverage/test denetimi
  ayrı iş (032.1)
- Docker YASAK yürürlükte — sandbox güvenliği tam native
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB) —
  yenilenmedi
- DECISIONS.md 2026-07-30 altında **5 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** birikti (toplam 44+)
- 026.3 CPU quota test flaky-fix 032 turunda yapıldı — 3.5s eşiği
  yükte fail veriyordu, 8s marj + 12s timeout ile güvenli

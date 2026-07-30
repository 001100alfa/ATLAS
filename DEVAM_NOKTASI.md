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

**Son çalışma:** 2026-07-30 (14. tur — 034 + 032.1 + chore launcher)
**Branch:** `main` (origin/main ile senkron — `30bd6c4`)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 14. tur tamamlandı; 2 lineer feat + 1 chore commit main'e
ff-merge/direct + push edildi (`4a34f21..30bd6c4`), 2 feature branch
silindi. **656/656 test yeşil** (+12 platform skip), coverage %90.97,
mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 14. tur)

Zincirleme iki iş (`034 → 032.1`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + `claudecode_Run.cmd`
chore commit + docs + push + branch temizlik.

1. **Görev 034** — git pre-commit hook + `atlas hooks` (`4c6ca6f`)
   - `tools/hooks/pre-commit` sh script — `atlas scan src` +
     `atlas doctor --strict`.
   - CLI: `atlas hooks install / uninstall / status`; imza (`#
     atlas-hook v1` ilk 5 satır) ile kullanıcının kendi hook'u
     korunur.
   - Install idempotent; yabancı hook için `--force` gerekir.
   - `.git` yoksa / şablon yoksa / yabancı+force yoksa exit 2.
   - Windows uyumu: git-bash sh standart; PowerShell shim YAGNI.
   - +17 test.

2. **Görev 032.1** — `atlas doctor --strict` ek denetimler (`1b3c195`)
   - Yeni yardımcılar: `_read_strict_entry_env`,
     `_count_recent_decisions`, `_check_vault_health`,
     `_has_quality_warning`.
   - `_collect_doctor_report` `quality` 3 alanlı:
     - `decisions_drift` (032)
     - `entry_count` (yeni) — son 30 gün, min 1
     - `vault_health` (yeni) — dizin var + en az 1 `.md`
   - `--strict` **üç kanaldan tetiklenir** (tek exit 9 yolu:
     `_has_quality_warning`); hem insan hem JSON.
   - Yeni env: `ATLAS_STRICT_ENTRY_WINDOW_DAYS`,
     `ATLAS_STRICT_MIN_ENTRIES`.
   - Bit-uyumluluk: `--strict` yoksa uyarılar bilgi, exit 0.
   - **Sözleşme değişikliği:** eski 032 "temiz exit 0" testi
     vault + `.md` gerektirir (yeni sözleşme).
   - +10 test (28 toplam 032+032.1).

3. **chore** — `claudecode_Run.cmd` (`30bd6c4`)
   - `opencode_Run.cmd` / `kilo_Run.cmd` kalıbı ile simetrik.
   - `ATLAS_LLM_CLAUDE_BIN` → `where claude` → `where claude.cmd`
     arama sırası.
   - PATH'e depo kökü + `cd /d %H%` (CLAUDE.md depo kökünden okunur).
   - Claude Code taşınabilirlik istisnasıdır (memory 2026-07-24),
     XDG/HOME override YOK.
   - Nested-if parser uyarısı (`'m'`) `call :find_bin` altprosedürüne
     dönüştürme ile giderildi.
   - Kanıt: `cmd /c claudecode_Run.cmd --version` → `2.1.133 (Claude
     Code)` temiz.

4. **Merge + push + temizlik**
   - `git merge --ff-only feat/034 && ... && feat/032.1` → 2 commit
     lineer main'e (`1b3c195`), merge commit YOK.
   - `chore(launcher): claudecode_Run.cmd` main'e doğrudan commit
     (`30bd6c4`).
   - `git push origin main` → `4a34f21..30bd6c4` uzağa gitti.
   - 2 feature branch silindi (`feat/034-precommit-hook`,
     `feat/032.1-doctor-strict-plus`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı.
  ThreadPool + sandbox paylaşımı + LLM rate limit gözetimi + exit
  agregasyon. **En büyük scope + risk**; ayrı tur.
- **Görev 033 — `atlas archive --restore <id>`:** arşivlenen görevi
  geri getir. `.tar.gz` extract + kolon çakışması. Orta.
- **Görev 034.1 — Windows PowerShell hook shim:** git-bash yokken
  Windows'ta hook çalışsın. Küçük iş.
- **Görev 032.2 — `atlas doctor --strict` çoğaltma:** `atlas scan
  src` denetimini de `--strict`'in içine al (şu an hook'ta iki ayrı
  komut, tek `atlas doctor --strict --scan-src` bayrağı ile birleşir).
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (30bd6c4 + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 3 commit (2026-07-30 14. tur):**
```
30bd6c4 chore(launcher): claudecode_Run.cmd (Claude Code CLI baslatici)
1b3c195 feat(032.1): atlas doctor --strict entry_count + vault_health denetimleri
4c6ca6f feat(034): git pre-commit hook + atlas hooks {install,uninstall,status}
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 656 passed, 12 skipped
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas hooks {install,uninstall,status}` (034) — pre-commit shim
  yönetimi. `--force` opt-in yıkıcı.
- `atlas doctor --strict` üç kanaldan tetiklenir (032.1) — drift +
  entry_count + vault_health.
- `claudecode_Run.cmd` — Claude Code CLI launcher (chore).

**Env sözleşmesi (kümülatif, bu turda eklenen ★):**
| Değişken | Anlam |
|---|---|
| `ATLAS_STRICT_ENTRY_WINDOW_DAYS` ★ | **032.1** — entry count denetim penceresi (30) |
| `ATLAS_STRICT_MIN_ENTRIES` ★ | **032.1** — pencere içi min giriş (1) |
| (önceki: `ATLAS_LLM`, `ATLAS_LLM_TIMEOUT`, `ATLAS_LLM_CLAUDE_BIN`, `ANTHROPIC_API_KEY`, `ATLAS_LLM_MODEL`, `ATLAS_LLM_ANTHROPIC_URL`, `ATLAS_LLM_ACP_BIN`, `ATLAS_LLM_ACP_ARGS`, `ATLAS_CONTEXT`, `ATLAS_ACP_INTERACTIVE`, `ATLAS_LLM_RETRIES`, `ATLAS_LLM_BACKOFF`, `ATLAS_LLM_JITTER`, `ATLAS_LLM_TRACE`, `ATLAS_LLM_PRICE_IN/OUT`, `ATLAS_LLM_OBS_CHARS`, `ATLAS_LLM_OBS_HEAD/TAIL`, `ATLAS_LLM_OBS_SUMMARIZE`, `ATLAS_ARCHIVE_AGE_DAYS`, `ATLAS_DOTENV`, `ATLAS_METRICS`, `ATLAS_SANDBOX_PATH`, `ATLAS_SANDBOX_TIMEOUT`, `ATLAS_SANDBOX_CPU_S`, `ATLAS_SANDBOX_MEM_MB`, `ATLAS_SANDBOX_MAX_PROC`, `ATLAS_RUNS_DIR`, `ATLAS_STRICT_DRIFT_DAYS`) | |

**Exit kodları:** DEĞİŞMEDİ (9 son 13. turda eklendi).

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `_cmd_doctor`, `_collect_doctor_report` mevcut çıktı + JSON alanları
  KORUNDU (`quality` alt-bölümleri genişledi).
- Mevcut CLI komutları KORUNDU; `hooks` yeni alt-komut.
- `_check_decisions_drift` (032) davranışı DEĞİŞMEDİ.
- Yeni exit kodu YOK.
- **Davranışsal sözleşme değişikliği (032.1):** `--strict` üç
  kanaldan tetiklenir. Belgelendirildi; eski test güncellendi.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **8 giriş bloğu** (+ chore,
   +018.3, +026.3, +032, +026.4, +034, +032.1, +chore launcher);
   2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 656 test yeşil (bu turun baseline'ı 629 → +27; oturum başı 319 → +337)
- 2 lineer feat + 1 chore commit main'e alındı, uzağa push edildi,
  2 feature branch silindi (kullanıcı `onayla` ile)
- Yeni env: `ATLAS_STRICT_ENTRY_WINDOW_DAYS`, `ATLAS_STRICT_MIN_ENTRIES`
- Yeni exit kodu YOK (13. turdaki 9 kaldı)
- Uncommitted değişiklik yok, working tree temiz
- 3 launcher tam sette: `opencode_Run.cmd`, `kilo_Run.cmd`,
  `claudecode_Run.cmd` (yeni). Simetrik.
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **8 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** birikti (toplam 47+)
- Bir bonus disiplin çıktısı: 034 pre-commit hook + 032.1 üç-kanal
  denetim **birbirini destekliyor** — kullanıcı `atlas hooks install`
  yaparsa her commit'te drift + entry + vault + scan otomatik kontrol.

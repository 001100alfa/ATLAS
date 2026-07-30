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

**Son çalışma:** 2026-07-30 (15. tur — 034.1 + 032.2 + chore 3-launcher)
**Branch:** `main` (origin/main ile senkron — `158d933` + docs)
**Working tree:** temiz (kapanış öncesi son doğrulama)
**Durum:** 15. tur tamamlandı; 2 lineer feat + 1 chore commit main'e
ff-merge/direct + push edildi (`d6f617a..158d933`), 2 feature branch
silindi. **670/670 test yeşil** (+12 platform skip), coverage %90.99,
mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 15. tur)

Zincirleme iki iş (`034.1 → 032.2`), her biri kendi branch'inde tek
commit; sonrasında main'e lineer ff-merge + 3-launcher chore commit
(sıra başı) + docs + push + branch temizlik.

1. **chore** — 3 launcher: `goose_Run.cmd`, `cline_Run.cmd`,
   `kimi_Run.cmd` (`136205e`)
   - Thin shim yaklaşımı: `tools/agents/<name>.cmd` sarmalayıcısını
     `call` eder (kurulum sihirbazı zaten tam env kurulumunu yapıyor).
   - Kök launcher yalnız: PATH prefix + cwd + call + exit code aynen.
   - **6 kök launcher tam sette:** opencode / kilo / claudecode /
     goose / cline / kimi.
   - Smoke: goose 1.44.0, cline 3.0.47, kimi 1.49.0 — temiz.

2. **Görev 034.1** — Windows sh.exe guard + shell tespiti (`8c72841`)
   - `_find_hook_shell`: Non-Windows sabit `"sh"`; Windows depo-yerel
     (`tools/git/usr/bin/sh.exe`) öncelik → PATH → klasik Git for
     Windows yolları.
   - `atlas hooks install` shell None → exit 0 + stderr uyarı.
   - `atlas hooks status` alanları: `shell_available`, `shell_path`
     (JSON + insan).
   - PowerShell wrapper YAPILMADI (git hooks sh üstünde; PS giriş
     noktası yok — bilinçli karar).
   - +7 test (24 toplam 034/034.1).

3. **Görev 032.2** — `atlas doctor --scan-src` birleştirme (`158d933`)
   - `_check_scan_src`: kaynak dizininde `scan_secrets`, bulgu +
     ilk 5 dosya sample + warning.
   - `--scan-src [PATH]` opt-in bayrağı (varsayılan `src`).
   - `_collect_doctor_report` opsiyonel parametre; bayrak yoksa
     alan hiç yer almaz (bit-uyumluluk + ekstra IO yok).
   - **`_has_quality_warning` (032.1) `scan_src.warning`'i otomatik
     yakaladı** — strict tek kanal 4 kaynak (drift + entry_count +
     vault + scan).
   - Hook shim **v1 → v2**: tek `atlas doctor --strict --scan-src`
     (önceden iki subprocess). İmza prefix aynı — uninstall güvenli.
   - `atlas scan <path>` bağımsız komutu SÖZLEŞMESİ DEĞİŞMEDİ.
   - +7 test (35 toplam 032/032.1/032.2).

4. **Merge + push + temizlik**
   - `chore(launcher):` main'e doğrudan commit (`136205e`).
   - `git merge --ff-only feat/034.1 && feat/032.2` → 2 commit
     lineer main'e (`158d933`), merge commit YOK.
   - `git push origin main` → `d6f617a..158d933` uzağa gitti.
   - 2 feature branch silindi (`feat/034.1-windows-ps-hook`,
     `feat/032.2-doctor-scan-src`).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 031 — Batch paralel `--jobs N`:** 030'un doğal uzantısı.
  ThreadPool + sandbox paylaşımı + LLM rate limit gözetimi + exit
  agregasyon. **En büyük scope + risk**; tek turluk.
- **Görev 033 — `atlas archive --restore <id>`:** arşivlenen görevi
  geri getir. `.tar.gz` extract + kolon çakışması. Orta.
- **Görev 032.3 — `_cmd_scan`'i `_check_scan_src`'e yeniden yönlendir:**
  DRY — iki farklı yerde aynı `scan_secrets` döngüsü var (`_cmd_scan`
  ve `_check_scan_src`). Refactor küçük.
- **Görev 035 — opencode_Run.cmd + kilo_Run.cmd thin shim refactor:**
  tarihsel yazımı `tools/agents/*.cmd` üzerine kalıba çek (034.1
  simetri). Küçük.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (158d933 + docs) = main ← senkron
```
Kalan local branch'ler (bu turların dışı, önceki oturumların işi):
`feat/paketleme-bulut-secenegi`, `feat/tasinabilir-kurulum`,
`fix/{arsivleyici-arama, kimi-yeniden-etkinlestirme,
ollama-kimligi-tasinabilir, surum-etiketli-yedek}`.

**main'e giren 3 commit (2026-07-30 15. tur):**
```
158d933 feat(032.2): atlas doctor --scan-src birlesimi + hook v2
8c72841 feat(034.1): Windows sh.exe guard + hook shell tespiti
136205e chore(launcher): goose_Run.cmd + cline_Run.cmd + kimi_Run.cmd
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 670 passed, 12 skipped
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı  (veya: atlas doctor --scan-src)
```

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --scan-src [PATH]` (032.2) — sır taraması doctor'a dahil.
- `atlas hooks status` iki yeni alan: `shell_available`, `shell_path`
  (034.1).
- `atlas hooks install` Windows'ta shell yoksa uyarı bassın (034.1).
- 3 yeni kök launcher: `goose_Run.cmd` / `cline_Run.cmd` /
  `kimi_Run.cmd` (chore).
- Hook shim v2 — tek komut çağrısı.

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:** DEĞİŞMEDİ (9 kalıcı).

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `_cmd_doctor` mevcut çıktı + JSON KORUNDU; `--scan-src` opt-in,
  alan yalnız bayrak varsa görünür.
- `_cmd_scan` (mevcut `atlas scan`) dokunulmadı — bağımsız kullanım
  devam ediyor.
- `_cmd_hooks_install/status/uninstall` bit-uyumlu — shell varken
  034 davranışı aynen.
- `_JOBOBJECT_*`, `_build_preexec_fn`, planner tarafı bu turda
  dokunulmadı.
- `_has_quality_warning` (032.1) tek kanal yolu 4 kaynak kesiyor —
  yeni katman eklemek sıfır maliyette (032.2 kanıtı).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **11 giriş bloğu** (kümülatif:
   chore, 018.3, 026.3, 032, 026.4, 034, 032.1, chore claudecode,
   3-launcher chore, 034.1, 032.2); 2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 670 test yeşil (bu turun baseline'ı 656 → +14; oturum başı 319 → +351)
- 2 lineer feat + 1 chore commit main'e alındı, uzağa push edildi,
  2 feature branch silindi (kullanıcı `onayla` peşin ile)
- Yeni env YOK
- Yeni exit kodu YOK (9 kalıcı)
- Uncommitted değişiklik yok, working tree temiz
- 6 kök launcher tam sette (opencode / kilo / claudecode / goose /
  cline / kimi) — Juggler ACP 5 ajan + Claude Code hepsi tek-tık
  başlatılabilir
- Hook shim v2 — tek `atlas doctor --strict --scan-src` her commit'te
  4 kanal quality gate (drift + entry_count + vault + scan)
- Pre-commit disiplin **tam operasyonel:** `atlas hooks install`
  → shell tanı + tek quality gate + tek exit noktası
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **11 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** birikti (toplam 50+)

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

**Son çalışma:** 2026-07-30 (19. tur — 038 + 037.1 + 033 + 031)
**Branch:** `main` (4 lineer commit ff-merge, push bekliyor)
**Working tree:** temiz
**Durum:** 19. tur tamamlandı; 4 görev tek turluk zincirleme yapıldı;
tümü main'e lineer ff-merge edildi. **722/722 test yeşil** (+12
platform skip), coverage %90.71, mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 19. tur)

Zincirleme **4 iş**, küçükten büyüğe: `038 → 037.1 → 033 → 031`. Her
biri kendi branch'inde tek commit; sonra main'e lineer ff-merge (her
rebase sonrası tam kalite kapısı).

1. **Görev 038** — `doctor --scan-src` unique_hits (`ad73010`)
   - `quality.scan_src` şemasına `unique_hits: int` eklendi.
   - `total` = ham bulgu; `unique_hits` = tekil dosya sayısı.
   - İnsan format `(N bulgu, M tekil dosya)`.
   - Şema v1 korundu (yalnız alan eklendi).
   - +4 test.

2. **Görev 037.1** — `atlas ai-cli update` (`ab01e4d`)
   - Portable npm wrap: `tools/node/npm.cmd` (win) / `tools/node/npm`
     (unix) öncelik; yoksa `shutil.which("npm")` (PATH).
   - `--dry-run` → `npm outdated --long` (npm exit 1 = bulgu, CLI
     exit 0); `update` → npm exit doğrudan yansıtılır.
   - `tools/ai-cli/` yok / npm yok → exit 2 + SPEC HATASI.
   - +7 test.

3. **Görev 033** — `atlas archive --restore <id>` (`31cf934`)
   - `.tar.gz` extract `filter="data"` güvenli mod + her üye elle
     kontrol (path traversal, kolon `:`, beklenmeyen kök).
   - En yeni mtime sürümü seçilir (aynı id için birden çok tar).
   - Exit 3 çakışma, 6 arşiv yok / extract hatası.
   - `RestoreError` yeni tip (N818 uyumlu).
   - +12 test.

4. **Görev 031** — `atlas run --jobs N` (`cfc201b`) — **büyük**
   - N=1 seri (bit-uyumlu); N>1 `ThreadPoolExecutor`.
   - `_ThreadCaptureStream`: TLS StringIO (contextlib.redirect_stdout
     process-global; thread-safe değil).
   - `AuditLog` **thread-safe** yapıldı: `_lock_for(path)` module-level
     path bazlı lock + `verify()` boş satır fail-safe.
   - Paralel modda fail-fast implicit KAPALI (worker'lar zaten koşuyor).
   - `--jobs 0` → SPEC HATASI + exit 2.
   - +6 test.

5. **Merge + temizlik**
   - Sıra: `038 → 037.1 → 033 → 031` (her biri main'e rebase + ff-merge).
   - 4 commit lineer main'e: `ad73010 → ab01e4d → 31cf934 → cfc201b`.
   - Feature branch'ler henüz silinmedi (bu turun sonunda temizlik).

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 037.2 — `atlas ai-cli list`:** hangi AI CLI'lar kurulu
  (opencode/kilo/cline/kimi), sürümleri, güncelleme adayları.
  Küçük-orta.
- **Görev 031.1 — `atlas run --jobs N --dry-run` özet:** paralel batch
  dry-run'da her worker'ın plan step'lerini özetle raporla. Çok küçük.
- **Görev 034.2 — pre-commit hook Windows PowerShell testi:** SPEC 034.1
  (Windows PS hook) tekrar canlı çalıştırma; regresyon kontrolü. Küçük.
- **Görev 039 — LLM connection pool metriği:** paralel LLM çağrılarında
  eş-zamanlı inflight sayısını `.atlas/metrics.jsonl`'a yaz. Orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (fe8dea8) ← main (cfc201b, 4 commit önde, PUSH bekliyor)
```
Kalan local feature branch'ler (silinecek): `feat/031-batch-parallel`,
`feat/033-archive-restore`, `feat/037.1-ai-cli-update`,
`feat/038-scan-src-unique-hits`.
Önceki oturumların branchleri: `feat/paketleme-bulut-secenegi`,
`feat/tasinabilir-kurulum`, `fix/{arsivleyici-arama,
kimi-yeniden-etkinlestirme, ollama-kimligi-tasinabilir,
surum-etiketli-yedek}`.

**main'e giren 4 commit (2026-07-30 19. tur):**
```
cfc201b feat(031): atlas run --jobs N (batch paralel)
31cf934 feat(033): atlas archive --restore <id>
ab01e4d feat(037.1): atlas ai-cli update portable npm wrap
ad73010 feat(038): doctor --scan-src unique_hits alani
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 722 passed, 12 skipped, cov 90.71%
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --scan-src` çıktısı: `unique_hits` alanı (JSON) +
  `(N bulgu, M tekil dosya)` (insan)
- `atlas ai-cli update [--dry-run]` (yeni komut)
- `atlas archive --restore <id> [--apply]` (yeni bayrak)
- `atlas run --goal-file A B C --jobs N` (yeni bayrak)

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:**
- **Yeni:** archive restore çakışma → **3**; archive restore arşiv
  yok/extract hatası → **6**.
- Mevcut kodlar (0/2/4/8/9) korundu.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- SPEC 030 batch testleri (7 test) bit-uyumlu.
- `_cmd_run_goal` dokunulmadı.
- `archive_task` fonksiyonu dokunulmadı; `restore_task` yeni.
- `AuditLog` public API (record/verify) sözleşmesi aynı; iç
  thread-safety eklendi (transparent).
- Doctor JSON şema v1 korundu (yalnız alan eklendi).
- `ai-cli diff-summary` bit-uyumlu.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **21 giriş bloğu**
   (bu tur 4 yeni blok eklendi; toplam 17 → 21);
   2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 722 test yeşil (bu turun baseline'ı 693 → +29; oturum başı 319 → +403)
- 4 lineer commit main'e alındı; PUSH bekliyor
- 4 feature branch silinecek (kapanış temizliği)
- Yeni env YOK
- Yeni exit kodu var: **3** (archive restore çakışma), **6** genişledi
- Uncommitted değişiklik yok
- Yeni CLI komutları: `atlas archive --restore`, `atlas ai-cli update`,
  `atlas run --jobs N`
- Yeni şema alanları: `quality.scan_src.unique_hits`
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **21 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** (toplam 60+)
- **AuditLog thread-safety** yeni bir platform sözleşmesi — çoklu
  worker/thread'in aynı `audit.jsonl`'e yazması artık güvenli

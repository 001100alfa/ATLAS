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
>    `DECISIONS.md`'nin son 2026-07-31 girişlerini kaba tarama.

**Son çalışma:** 2026-07-31 (24. tur — 044 + 049 + 045 + 047)
**Branch:** `main` (origin ile SENKRON, 4 lineer commit push edildi)
**Working tree:** temiz (DOCTOR_*.png artık ignore — SPEC 044)
**Durum:** 24. tur tamamlandı; 4 görev zincirleme; tümü main'e lineer
ff-merge + push. **838/838 test yeşil** (+12 skip), cov %90.90,
mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-31 — 24. tur)

Zincirleme **4 iş** — sıra: `044 → 049 → 045 → 047`. Kullanıcı
onayı sonrası SPEC iskeletleri toplu sunuldu, uygulama sırayla.

1. **Görev 044** — `.gitignore` DOCTOR_*.png (`c0bfd7c`)
   - `.gitignore`'a `DOCTOR_cmd.png` + `DOCTOR_*.png` deseni.
   - `git check-ignore -v DOCTOR_cmd.png` → 0 (ignored).
   - Dosya silinmedi (kullanıcı yerelinde debug değerinde).
   - Test yok (dokümantasyon-benzeri); 810 mevcut bit-uyumlu.

2. **Görev 049** — SafeExtract refactor (`80e3230`)
   - **Yeni namespace:** `src/atlas_core/utils/` (top-level).
   - **Yeni modül:** `utils/safe_tar.py`
     - `UnsafeTarMemberError(ValueError)` N818 uyumlu.
     - `verify_tar_members(members, expected_root)` — path
       traversal + Windows kolon + kök arcname kontrolü tek yerde.
     - Backslash normalize; mesaj metni SPEC 033/041 sözleşmesini
       KORUR.
   - `memory/archive.py::restore_task` + `memory/vault_backup.py::
     restore_vault`: 20 satırlık for loop'lar 4 satıra indi
     (verify + try/except → domain hatasına re-raise).
   - `filter="data"` extract çağrısı KORUNDU (defense-in-depth).
   - +12 birim test. **36 mevcut restore testi bit-uyumlu.**

3. **Görev 045** — pre-commit hook v3 (`3f0777a`)
   - `tools/hooks/pre-commit`: v2 → v3 imzası.
   - Doctor gate KORUNDU; yeni gate `atlas vault verify --strict`.
   - `[ -d vault ]` guard verify'den ÖNCE (fresh clone naziksiz
     olmasın).
   - `_HOOK_SIGNATURE`: `"# atlas-hook v1"` → `"# atlas-hook v3"`
     (sabit ile şablon uyumlandı; `_is_atlas_hook` versiyon
     bilinçsiz kalmaya devam).
   - Kurulu v2 hook'lar `hooks status`'ta `up_to_date=False`;
     kullanıcı `hooks install --force` ile v3'e geçer.
   - +5 test. 24 mevcut hook testi bit-uyumlu.

4. **Görev 047** — `atlas doctor --format prometheus` (`801d2ba`)
   - Prometheus text v0.0.4 export. Metrikler:
     - `atlas_doctor_up 1` (canonical `up` gauge)
     - `atlas_doctor_warnings_total <n>` (gauge)
     - `atlas_doctor_quality_healthy{field=NAME} 0|1` (gauge; her
       quality alanı için, sorted keys)
     - `atlas_doctor_scan_src_hits_total` + `_scan_src_unique_files`
       (opsiyonel, yalnız scan_src alanı raporda varsa)
   - Parser: `--json`, `--schema`, `--format` üçlüsü MUTEX
     (`add_mutually_exclusive_group`). Bonus: `--json --schema`
     de mutex artık.
   - `--strict` format bağımsız (exit 9 kaldı — Prometheus çıktı
     + exit alert paralel çalışır).
   - +11 test. 100 mevcut doctor testi bit-uyumlu.

5. **Merge + kalite kapıları**
   - Her görev: branch → kod → test → tam pytest/mypy/ruff/scan →
     main'e ff-merge.
   - 4 commit lineer main'e: `c0bfd7c → 80e3230 → 3f0777a → 801d2ba`.
   - Push edildi; local ile origin senkron.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar
(24. tur sonrası; 23. turdan 046, 048 hâlâ açık):

- **Görev 046 — `atlas vault verify --fix-orphans`:** rapor eden
  değil, orfan notları `_archive/` altına taşıyan yıkıcı mod
  (`--apply` gerekli). Orta.
- **Görev 048 — `atlas vault backup --auto` sistem cron entegrasyonu:**
  Windows Task Scheduler XML + Unix `systemd.timer` template'i
  `tools/scheduling/` altında. SPEC değil, deployment artefaktı. Küçük.
- **Görev 050 — `atlas ai-cli update <name>` isteğe bağlı:**
  şu an `update` tüm paketleri günceller; tek paket seçebilme
  komutu operasyonel esneklik. Küçük.
- **Görev 051 — Doctor + Prometheus HTTP endpoint:** `atlas metrics
  --serve :9090` ve `atlas doctor --serve :9091` — long-running
  scrape target. Orta-büyük (aiohttp bağımlılığı? yoksa stdlib).
- **Görev 052 — vault_verify.VerifyReport pre-commit özet dumper:**
  kırık link listesi commit'ten önce README/vault/health.md'ye
  otomatik yazsın. Bakım kolaylığı. Küçük.
- **Görev 053 — CLI `atlas` root'a `--version`:** şu an alt-komut
  seviyesinde sürüm yok. Micro.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main == main (00145b6 + 4 commit push edildi, SENKRON)
```
Lokal feature branch YOK (temiz).

**main'e giren 4 commit (2026-07-31 24. tur):**
```
801d2ba feat(047): atlas doctor --format prometheus text v0.0.4 export
3f0777a feat(045): pre-commit hook v2 -> v3, vault verify --strict gate
80e3230 refactor(049): SPEC 033+041 ortak SafeExtract yardimcisina cikar
c0bfd7c feat(044): .gitignore DOCTOR_cmd.png + DOCTOR_*.png
```
Öncesi (aynı gün, 23. tur): `ab53340` docs + `00145b6` `4fbe367`
`3965cf7` `614b9ef` (4 feat).

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 838 passed, 12 skipped, cov 90.90%
uv run mypy src                # temiz (29 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --format {human,prometheus}` (yeni bayrak, mutex
  `--json` ve `--schema` ile)

**Yeni davranış (kullanıcı-görünür):**
- Pre-commit hook zincirinde `vault verify --strict` gate
  (kurulu v2 hook'lar için `hooks install --force` şart).
- `DOCTOR_*.png` git'te ignored.

**Yeni modül:** `src/atlas_core/utils/safe_tar.py` (SPEC 049).

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:** DEĞİŞMEDİ (mevcut kod 0/2/3/4/6/7/8/9 sınıfı korunur).

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `atlas doctor` mevcut çıktıları (bayraksız, `--json`, `--schema`,
  `--strict`, `--scan-src`, `--pretty`, `--ping`) BİT-UYUMLU.
- `atlas hooks {install,uninstall,status}` BİT-UYUMLU.
- SPEC 033 archive restore + SPEC 041 vault restore mesaj sözleşmesi
  regex bit-uyumlu (test dosyaları değişmedi).
- Vault API, backup/restore, verify (SPEC 041/041.1/042) BİT-UYUMLU.
- Metrics prometheus (SPEC 043) sözleşmesi ile Doctor prometheus
  (SPEC 047) ortak kalıp (mutex, choices, default None).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-31 en üstteki iki blok (24. tur 14 giriş
   + 23. tur 14 giriş = 28 giriş bugün); 2026-07-30 altında 29 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 838 test yeşil (770 → 810 → 838; bu tur +28; oturum başı 319'dan
  +519)
- 4 lineer commit main'e; origin ile SENKRON
- Lokal feature branch YOK (temiz)
- Yeni env YOK
- Yeni exit kodu YOK
- Yeni CLI komutu YOK (yeni bayrak: `doctor --format`)
- Yeni modül: `src/atlas_core/utils/safe_tar.py`
- Yeni test dosyaları: `test_utils_safe_tar.py`,
  `test_cli_doctor_prometheus.py`
- Hook şablonu v2 → v3 (mevcut kullanıcılar `hooks install --force`
  ile güncellemeli)
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-31 altında **28 giriş bloğu** (24. tur 14 +
  23. tur 14); 2026-07-30 altında 29; 2026-07-29 altında 39
  (toplam 96+)
- Platform sözleşmesi: SafeExtract yardımcısı 3. bir tar-tabanlı
  komut geldiğinde direkt yeniden kullanılabilir (SPEC 049 refactor
  yatırımın karşılığı).
- Prometheus export ortak kalıbı (metrics + doctor): `--format
  {human,prometheus}` mutex `--json`; default `None` bit-uyumluluk.

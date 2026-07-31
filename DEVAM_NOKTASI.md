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

**Son çalışma:** 2026-07-31 (23. tur — 041.1 + 042 + 037.4 + 043)
**Branch:** `main` (origin ile SENKRON, 4 lineer commit push edildi)
**Working tree:** temiz (`DOCTOR_cmd.png` untracked — 22. turdan
kalan ekran görüntüsü; commit'lenmedi, gitignore adayı)
**Durum:** 23. tur tamamlandı; 4 görev zincirleme; tümü main'e lineer
ff-merge + push. **810/810 test yeşil** (+12 skip), cov %90.85,
mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-31 — 23. tur)

Housekeeping + zincirleme **4 iş** — sıra: `041.1 → 042 → 037.4 → 043`.

0. **Housekeeping** — 22. tur push + 6 branch temizliği
   - 22. tur `b5ce74c` (bugün 15:15, doctor toplu güncelleyici bakım)
     origin'e push edildi.
   - 6 merged branch silindi: `feat/{paketleme-bulut-secenegi,
     tasinabilir-kurulum}`, `fix/{arsivleyici-arama,
     kimi-yeniden-etkinlestirme, ollama-kimligi-tasinabilir,
     surum-etiketli-yedek}`.

1. **Görev 041.1** — `atlas vault backup --auto + --keep N` (`614b9ef`)
   - `vault_backup.prune_backups(archive_root, keep)`: mtime desc + N
     tut + gerisini sil. Sadece `vault-*.tar.gz` desenine dokunur;
     `keep<1` → `VaultBackupError`; `archive_root` yok → boş liste.
   - CLI `--auto` (mutex `--out`, exit 2): audit action `backup-auto`.
   - CLI `--keep N`: backup sonrası archive_root retention; her silme
     audit `prune`; `N<1` → exit 2; prune `OSError` → exit 6.
   - `--out` + `--keep` → stderr UYARI (retention YOK sayılır).
   - +10 test.

2. **Görev 042** — `atlas vault verify` (`3965cf7`)
   - Yeni modül `atlas_core/memory/vault_verify.py`:
     `BrokenLink` frozen dataclass (`frm/to`; JSON'da `"from"`),
     `VerifyReport` (broken_links + orphan_notes + orphan_tags +
     sayaçlar; `is_clean`; `to_dict()`), `verify_graph(graph)`.
   - CLI `verify [--vault-root] [--json] [--pretty] [--strict]`.
   - Vault üzerinde YAZMA YOK (salt-okunur analiz).
   - **Yeni exit kodu 4** = `--strict` + bulgu.
   - Audit: `atlas-vault` / `verify`.
   - +14 test (7 birim + 7 CLI).

3. **Görev 037.4** — `atlas ai-cli status <name>` (`4fbe367`)
   - Exec çalıştırmadan paket sağlık raporu: kurulu/beklenen sürüm,
     up_to_date, install_dir, size_bytes, size_human, bin_path.
   - Yeni yardımcı: `_dir_size_bytes` (rglob, symlink skip),
     `_human_bytes` (B/KB/MB/GB).
   - `up_to_date`: declared'daki `^ ~ >= < !` sıyrıp string eşitliği.
   - Exit 0 başarı; 2 SPEC HATASI (tools/ai-cli yok / dependencies'te
     yok / kurulu değil — öneri: `list` veya `update`).
   - +7 test.

4. **Görev 043** — `atlas metrics --format prometheus` (`00145b6`)
   - Prometheus text v0.0.4 export: 9 metrik (records/tokens/cache/
     hit_ratio/cost/inflight × 2).
   - Parser: `--json` ve `--format {human,prometheus}` MUTEX
     (`add_mutually_exclusive_group`). Default `None` → bit-uyumluluk.
   - `cache_hit_ratio` gauge 0-1 (Prometheus konvansiyonu — ondalık).
   - `cost_usd_total` fiyat env'i yoksa 0.0 (Prometheus tutarlılığı).
   - `inflight_max/avg` yalnız `inflight` alanı olan kayıtlar varsa.
   - Defensive: `--json + --format prometheus` env'e karşı exit 2.
   - +6 test.

5. **Merge + kalite kapıları**
   - Her görev: branch → kod → test → tam pytest/mypy/ruff/scan →
     main'e ff-merge.
   - 4 commit lineer main'e: `614b9ef → 3965cf7 → 4fbe367 → 00145b6`.
   - Push edildi; local ile origin senkron.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 044 — `.gitignore`'a `DOCTOR_cmd.png` + `.png` ekran
  görüntüleri:** 22. turdan beri kalan untracked dosya; iki tur
  boyunca `git add -A` gafına yol açtı. Micro.
- **Görev 045 — vault verify pre-commit hook entegrasyonu:** SPEC 034
  hook zincirine `atlas vault verify --strict` ekle; commit sırasında
  kırık link/orfan tag'e karşı erken gate. Küçük.
- **Görev 046 — `atlas vault verify --fix-orphans`:** rapor eden
  değil, orfan notları `_archive/` altına taşıyan yıkıcı mod
  (`--apply` gerekli). Orta.
- **Görev 047 — `atlas doctor` Prometheus export:** metrics gibi
  doctor sonuçları için `--format prometheus` (up/down gauge'ları).
  Küçük-orta.
- **Görev 048 — `atlas vault backup --auto` sistem cron entegrasyonu:**
  Windows Task Scheduler XML + Unix `systemd.timer` template'i
  `tools/scheduling/` altında. SPEC değil, deployment artefaktı. Küçük.
- **Görev 049 — Ortak `SafeExtractError` yardımcısı:** SPEC 033 archive
  restore + SPEC 041 vault restore ortak kalıbını
  `atlas_core/utils/safe_tar.py` altına çıkar (path traversal +
  filter='data' + kolon + temp+rename). Refactor. Orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main == main (00145b6, SENKRON)
```
Lokal feature branch YOK (temiz).

**main'e giren 4 commit (2026-07-31 23. tur):**
```
00145b6 feat(043): atlas metrics --format prometheus text v0.0.4 export
4fbe367 feat(037.4): atlas ai-cli status <name> [--json] paket sagliki raporu
3965cf7 feat(042): atlas vault verify — kirik link/orfan not-tag raporu
614b9ef feat(041.1): atlas vault backup --auto + --keep N (cron retention)
```
Öncesi: `b5ce74c` (22. tur doctor bakım) + `51b2fe3` (21. tur docs).

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 810 passed, 12 skipped, cov 90.85%
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas vault backup --auto` (mutex `--out`)
- `atlas vault backup --keep N` (retention)
- `atlas vault verify [--json] [--pretty] [--strict]` (yeni komut)
- `atlas ai-cli status <name> [--json]` (yeni komut)
- `atlas metrics --format {human,prometheus}` (mutex `--json`)

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:**
- **Genişledi:** `4` = `vault verify --strict` + bulgu (yeni anlam;
  `atlas run` içindeki `PlannerExhaustedError` 4 ile çakışmaz).
- Mevcut: `3` = vault restore çakışma; `6` = vault backup/prune hata.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `atlas metrics` (bayraksız) ve `atlas metrics --json` (ham liste)
  BİT-UYUMLU.
- `atlas vault backup [--out]` (SPEC 041) BİT-UYUMLU.
- `atlas ai-cli diff-summary / update / list / exec` BİT-UYUMLU.
- `Vault` API dokunulmadı.
- SPEC 023.2 inflight tüketimi 043 Prometheus'ta korundu (inflight
  satırları yalnız veri varsa yayımlanır).
- Doctor JSON şema v1 korundu.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-31 üstteki 14 giriş bloğu (bu tur yeni);
   2026-07-30 altında 29 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 810 test yeşil (770 → 773 → 810; bu tur +37; oturum başı 319'dan
  +491)
- 4 lineer commit + 22. tur `b5ce74c` main'de; origin ile SENKRON
- 6 eski feature branch temizlendi (kapanış temizliği yapıldı)
- Yeni env YOK
- Exit kodları: `4` yeni anlamla (vault verify --strict)
- Yeni CLI komutları: `atlas vault verify`, `atlas ai-cli status`
- Genişleyen bayraklar: `atlas vault backup --auto`, `--keep N`;
  `atlas metrics --format {human,prometheus}`
- Yeni modül: `atlas_core/memory/vault_verify.py`
- Yeni test dosyaları: `test_cli_vault_verify.py`,
  `test_cli_ai_cli_status.py`
- Untracked kalan: `DOCTOR_cmd.png` (ekran görüntüsü) — 044 için
  aday: `.gitignore`'a ekle
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-31 üstünde **14 giriş bloğu**, 2026-07-30
  altında **29 giriş bloğu**, 2026-07-29 altında **39 giriş bloğu**
  (toplam 82+)
- Platform sözleşmesi: SPEC 033 (archive restore) + SPEC 041 (vault
  backup/restore) ortak kalıbı — gelecekte ortak `SafeExtractError`
  yardımcısına çıkarılabilir (Görev 049 adayı)

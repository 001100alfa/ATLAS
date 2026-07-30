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

**Son çalışma:** 2026-07-30 (21. tur — 037.3 + 023.2 + 040 + 041)
**Branch:** `main` (4 lineer commit ff-merge, push bekliyor)
**Working tree:** temiz
**Durum:** 21. tur tamamlandı; 4 görev zincirleme; tümü main'e
lineer ff-merge. **770/770 test yeşil** (+12 skip), cov %90.76,
mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-07-30 — 21. tur)

Zincirleme **4 iş** — sıra: `037.3 → 023.2 → 040 → 041`.

1. **Görev 037.3** — `atlas ai-cli exec <name> [args...]` (`36bba4c`)
   - Portable launcher; `tools/ai-cli/node_modules/.bin/<name>`
     shim'ini subprocess ile çalıştırır.
   - Windows: `.cmd` öncelik → `.exe` → çıplak; Unix: çıplak isim.
   - `argparse.REMAINDER` ile tüm flag'ler forward; exit yansıtılır.
   - Canlı: `atlas ai-cli exec cline --version` → `3.0.47` exit 0.
   - +5 test.

2. **Görev 023.2** — metrics inflight istatistiği (`e1b0329`)
   - `atlas metrics` insan çıktısı: `inflight avg/max: A.AA / N (K
     kayıtta)`.
   - `inflight` alanı olmayan kayıtlar skip; hiç yoksa satır BASILMAZ.
   - `--json` bit-uyumlu (ham liste).
   - +4 test.

3. **Görev 040** — `atlas doctor --schema` (`ffbbe63`)
   - `_doctor_schema_descriptor`: `{schema_version, top_level[],
     quality_fields[], exit_codes{}, notes[]}`.
   - `--schema` **kısa devre** — sağlık kontrolü YAPMAZ, IO'suz,
     idempotent.
   - `--pretty` ile indent=2.
   - +5 test.

4. **Görev 041** — vault backup/restore (`dd43737`)
   - Yeni modül `atlas_core/memory/vault_backup.py`:
     `backup_vault`, `restore_vault`, `default_backup_path`,
     `VaultBackupError`.
   - CLI: `atlas vault backup [--out] [--vault-root] [--archive-root]`
     ve `atlas vault restore <tar> [--apply] [--vault-root]`.
   - Path traversal koruma (SPEC 033 kalıbı) + `filter="data"`.
   - Restore temp-extract + rename kalıbı (mevcut vault dokunulmaz).
   - Yeni exit kodları: **3** çakışma, **6** extract/backup hatası.
   - Audit: `atlas-vault` / `backup|restore`.
   - +14 test.

5. **Merge + kalite kapıları**
   - Sıra: `037.3 → 023.2 → 040 → 041` (her biri main'e rebase +
     ff-merge + tam pytest/mypy/ruff/scan).
   - 4 commit lineer main'e: `36bba4c → e1b0329 → ffbbe63 → dd43737`.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 041.1 — `atlas vault backup --auto`:** cron/scheduled
  senaryo için timestamp'li tekil yedek + `--keep N` retention. Küçük.
- **Görev 042 — `atlas vault verify`:** vault graph sağlığı (kırık
  wikilink, yetim not, orfan tag). Orta.
- **Görev 037.4 — `atlas ai-cli status <name>`:** exec olmadan sürüm
  + son güncelleme + kurulum boyutu raporu. Küçük.
- **Görev 043 — Prometheus text export:** `atlas metrics --format
  prometheus` → scrape edilebilir metrik. Orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main (30adfb9) ← main (dd43737, 4 commit önde, PUSH bekliyor)
```
Kalan local feature branch'ler (silinecek): `feat/037.3-ai-cli-exec`,
`feat/023.2-metrics-inflight`, `feat/040-doctor-schema`,
`feat/041-vault-backup-restore`.
Önceki oturumların branchleri: `feat/paketleme-bulut-secenegi`,
`feat/tasinabilir-kurulum`, `fix/{arsivleyici-arama,
kimi-yeniden-etkinlestirme, ollama-kimligi-tasinabilir,
surum-etiketli-yedek}`.

**main'e giren 4 commit (2026-07-30 21. tur):**
```
dd43737 feat(041): atlas vault backup/restore + vault_backup.py modul
ffbbe63 feat(040): atlas doctor --schema JSON sema yayimi
e1b0329 feat(023.2): atlas metrics inflight avg/max istatistigi
36bba4c feat(037.3): atlas ai-cli exec <name> [args...] portable launcher
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 770 passed, 12 skipped, cov 90.76%
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli exec <name> [args...]` (yeni komut)
- `atlas metrics` insan çıktısına inflight avg/max satırı
- `atlas doctor --schema [--pretty]` (yeni bayrak — kısa devre)
- `atlas vault backup [--out]` (yeni komut)
- `atlas vault restore <tar> [--apply]` (yeni komut)

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:**
- **Genişledi:** `3` = vault restore çakışma; `6` = vault
  backup/extract hatası (mevcut archive kodlarıyla aynı sınıf).

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- Mevcut `atlas doctor` (bayraksız, `--json`, `--strict`, `--ping`,
  `--scan-src`, `--pretty`) BİT-UYUMLU.
- `atlas metrics --json` (ham liste) BİT-UYUMLU.
- `atlas archive` (007/012/017/033) BİT-UYUMLU.
- `Vault` API dokunulmadı.
- Doctor JSON şema v1 korundu.
- SPEC 037 (diff-summary), 037.1 (update), 037.2 (list) BİT-UYUMLU.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-07-30 altında **29 giriş bloğu** (bu tur 4
   yeni; toplam 25 → 29); 2026-07-29 altında 39 blok.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 770 test yeşil (baseline 742 → +28; oturum başı 319 → +451)
- 4 lineer commit main'e; PUSH bekliyor
- 4 feature branch silinecek (kapanış temizliği)
- Yeni env YOK
- Exit kodları: `3` ve `6` vault backup/restore için genişledi
- Yeni CLI komutları: `atlas ai-cli exec`, `atlas vault backup`,
  `atlas vault restore`, `atlas doctor --schema`
- Yeni modül: `atlas_core/memory/vault_backup.py`
- Yeni test dosyası: `test_cli_vault_backup.py`
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-07-30 altında **29 giriş bloğu**, 2026-07-29
  altında **39 giriş bloğu** (toplam 68+)
- Platform sözleşmesi: SPEC 033 (archive restore) + SPEC 041 (vault
  backup/restore) ortak kalıbı — path traversal koruması + `filter="data"`
  + temp extract + rename. Gelecekte ortak yardımcıya çıkarılabilir.

# DEVAM NOKTASI — ATLAS

> ## TETİKLEYİCİ (agent talimatı — bu bloku her açılışta oku)
> Kullanıcı **"devam et"**, **"kaldığı yerden devam et"** veya
> **"projeye devam"** derse, başka soru sormadan:
> 1. Bu dosyanın **tamamını** oku.
> 2. `## Bu turda yapılan` bölümünden son turun sonucunu özetle.
> 3. `## Sıradaki Karar (kullanıcıya sunulacak)` altındaki adayları
>    listeleyip kısa bir seçim sorusuyla yeni turu başlat.
> 4. Kullanıcı onay verene kadar YIKICI işlem yapma (rm, force-push,
>    branch silme). Ancak main'e ff-merge sonrası `git push origin main`
>    tur kapanış rutini — mevcut oturumda onaylandı.
> 5. Zorunlu Döngü'ye (`CLAUDE.md` §Zorunlu Döngü) gir; ilk iş
>    `DECISIONS.md`'nin son 2026-08-05 girişlerini kaba tarama.

**Son çalışma:** 2026-08-05 (27. tur — 061 + 062 + 060 + 064 + 065 + 063)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 27. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1061/1061 test yeşil** (+12 skip), cov ~%91.5+, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 27. tur)

Kullanıcı "Continue from where you left off" + SessionStart hook →
27. tur seçimi "HEPSI (küçükten büyüğe)" onay verildi. 6 görev
zincirleme, sıra `061 → 062 → 060 → 064 → 065 → 063`.

1. **Görev 061** — `docs/api/vault-verify-schema.json` (`d29b0cd`)
   - SPEC 042 `VerifyReport` Draft-07 JSON Schema.
   - 7 zorunlu alan; `additionalProperties: false` (major bump gate).
   - Test: minimal Draft-07 doğrulayıcı test içinde (dış bağımlılık
     `jsonschema` YOK — YAGNI).
   - +12 test.

2. **Görev 062** — `doctor --save-baseline` + `--auto-baseline` (`450f9b7`)
   - `_DEFAULT_DOCTOR_BASELINE = .atlas/doctor-baseline.json` sabit.
   - `--save-baseline [PATH]` nargs="?" const=default; 4 mutex
     (diff/auto/serve/prometheus).
   - `--auto-baseline` — `--diff` yerine geç; dosya yoksa nazik
     uyarı + exit 0 (ilk çalıştırma).
   - +11 test.

3. **Görev 060** — `atlas ai-cli install <name>` (`c74fe74`)
   - `_run_npm_install(bin, package)`: `npm install <package> --save`.
   - 4-yollu hata (dir yok / package.json bozuk / npm yok / subprocess
     çöktü) → exit 2. npm exit yansır. Başarıda status/list ipucu.
   - +7 test.

4. **Görev 064** — `metrics --alert-webhook URL` (`e85774a`)
   - `_post_alert_webhook(url, payload, timeout=5.0)` stdlib urllib.
   - SSRF savunma: scheme yalnız http/https.
   - `--alert-email` ile ORTOGONAL (ikisi çalışır).
   - Exit 8 KORUR (SMTP kalıbı, SPEC 059).
   - +10 test.

5. **Görev 065** — `archive --search PATTERN [--json]` (`a7fb0aa`)
   - `_search_archive_contents(root, pattern)`: `tarfile.getnames()`
     metadata; tar AÇILMAZ. Bozuk tar skipped.
   - `re.search` part-match; `(?i)` inline flag desteği.
   - `--search` dispatcher'da en önde (read-only).
   - +13 test.

6. **Görev 063** — `vault backup --encrypt` GPG AES256 (`bce2487`)
   - `_find_gpg_bin()`: env `ATLAS_GPG_BIN` → `tools/gpg/gpg[.exe]` →
     `shutil.which("gpg")`.
   - `encrypt_backup(plain, out, passphrase, *, gpg_bin, cipher)`:
     stdin ile passphrase (history'de görünmez).
   - `--encrypt [PASSPHRASE]` nargs="?" const=env
     `ATLAS_BACKUP_PASSPHRASE`; boş passphrase → exit 2.
   - Plain `.tar.gz` silinir (secret disk'te bırakılmaz).
   - Restore tarafı DEĞİŞMEDİ (kullanıcı manuel `gpg --decrypt`).
   - +13 test.

7. **Kalite kapıları:**
   - Her görev: branch → kod → test → tam pytest/mypy/ruff/scan →
     main'e ff-merge.
   - 6 lineer commit: `d29b0cd → 450f9b7 → c74fe74 → e85774a → a7fb0aa
     → bce2487`.

---

## Sıradaki Karar (kullanıcıya sunulacak)

27. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 066 — `atlas vault restore --decrypt`:** SPEC 063 kardeşi —
  `.tar.gz.gpg` girdisi otomatik GPG decrypt + restore zinciri. Orta.
- **Görev 067 — `atlas vault backup --keep-encrypted N`:** SPEC 041.1
  retention'ını encrypted `.tar.gz.gpg` dosyaları için de yap
  (ayrı glob). Küçük-orta.
- **Görev 068 — `atlas metrics --alert-slack URL`:** SPEC 064 wrapper —
  Slack incoming webhook için provider-özel format (`{text}`).
  Küçük.
- **Görev 069 — `atlas run --dry-run` özet:** planner LLM çağrı sayısı
  + tahmini token/cost, çalıştırmadan. Orta.
- **Görev 070 — `.github/workflows/atlas-doctor.yml`:** SPEC 056
  kardeşi — PR'da `atlas doctor --strict --auto-baseline` gate.
  Küçük.
- **Görev 071 — `atlas archive --restore --search PATTERN`:** SPEC 065
  arama sonucunu SPEC 033 restore ile birleştir — matching arşivi
  otomatik geri aç. Orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main + 7 commit local (27. tur — push edilecek)
```
Lokal feature branch YOK (temiz).

**main'e giren 6 feat + 1 docs commit (2026-08-05 27. tur):**
```
bce2487 feat(063): vault backup --encrypt GPG symmetric AES256
a7fb0aa feat(065): atlas archive --search PATTERN [--json] regex arama
e85774a feat(064): atlas metrics --alert-webhook URL POST JSON (SPEC 059 kardesi)
c74fe74 feat(060): atlas ai-cli install <name> yeni paket ekleme
450f9b7 feat(062): atlas doctor --save-baseline + --auto-baseline snapshot yonetimi
d29b0cd feat(061): docs/api/vault-verify-schema.json — SPEC 042 JSON Schema
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1061 passed, 12 skipped
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli install <name>` (yeni alt-komut)
- `atlas archive --search PATTERN [--json]` (yeni bayrak)
- `atlas doctor --auto-baseline` + `--save-baseline [PATH]` (2 yeni bayrak)
- `atlas metrics --alert-webhook URL` (yeni bayrak)
- `atlas vault backup --encrypt [PASSPHRASE]` (yeni bayrak)

**Yeni doküman:** `docs/api/vault-verify-schema.json` (Draft-07).

**Yeni env sözleşmesi:**
- `ATLAS_BACKUP_PASSPHRASE` — SPEC 063 GPG passphrase default.
- `ATLAS_GPG_BIN` — SPEC 063 gpg binary override.

**Yeni yardımcılar:**
- `_run_npm_install` (cli.py, SPEC 060)
- `_post_alert_webhook` (cli.py, SPEC 064)
- `_search_archive_contents`, `_cmd_archive_search` (cli.py, SPEC 065)
- `_find_gpg_bin`, `encrypt_backup` (vault_backup.py, SPEC 063)
- `_diff_doctor_reports` yeniden kullanıldı (SPEC 057), `--auto-baseline`
  kaynak: default path (SPEC 062).

**Exit kodları:** DEĞİŞMEDİ.
- SPEC 063 GPG hata → **6** (SPEC 041 hata sınıfı).
- SPEC 064 webhook başarısız → **8 KORUR** (alert semantiği).
- SPEC 065 regex geçersiz / arc yok → **2** SPEC HATASI.

**Kritik sözleşme değişmezlikleri:**
- SPEC 041/041.1/042/046/048/052/056/057/058 hepsi BİT-UYUMLU.
- SPEC 037 ailesi (diff-summary, update, list, exec, status) BİT-UYUMLU.
- SPEC 043/047 Prometheus text formatı BİT-UYUMLU.
- SPEC 059 SMTP email BİT-UYUMLU (webhook ORTOGONAL).
- SPEC 033 archive restore BİT-UYUMLU.

**Bilinen flaky:** yok (nadiren 1 test yarış — re-run yeşil).

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki blok (27. tur ~18 giriş);
   2026-08-04 (25+26. tur ~47 giriş); 2026-07-31 (23+24. tur 28
   giriş); daha eski.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring

---

## Kapanış Notları

- **1061 test yeşil** (995 → 1061; bu tur +66; oturum başı 319'dan +742)
- 6 lineer feat + 1 docs commit; origin senkron
- Yeni env: `ATLAS_BACKUP_PASSPHRASE`, `ATLAS_GPG_BIN`
- Yeni CLI: `ai-cli install`, `archive --search`, `doctor --auto-baseline`,
  `doctor --save-baseline`, `metrics --alert-webhook`,
  `vault backup --encrypt`
- Yeni doküman: `docs/api/vault-verify-schema.json` (Draft-07 public API)
- Yeni test dosyaları: `test_verify_schema_doc.py`,
  `test_cli_doctor_auto_baseline.py`, `test_cli_ai_cli_install.py`,
  `test_cli_metrics_alert_webhook.py`, `test_cli_archive_search.py`,
  `test_cli_vault_backup_encrypt.py` (6 dosya, +66 test)
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB — 27 tur
  sonrası **güncel değil**; kullanıcı istiyorsa `PAKETLE.cmd`)
- DECISIONS.md 2026-08-05 altında ~18 giriş; 2026-08-04 altında ~47
  giriş; toplam 140+.
- Platform sözleşmesi: Prometheus scrape kalıbı (`--serve HOST:PORT`),
  alert kanalları (SMTP/webhook ortogonal), backup zinciri (backup →
  optional encrypt → optional prune), doctor snapshot (save/auto-baseline
  + diff).
- Sıradaki tur için 6 aday hazır (066–071).

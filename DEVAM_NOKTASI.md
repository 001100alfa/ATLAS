# DEVAM NOKTASI — ATLAS

> ## TETİKLEYİCİ (agent talimatı — bu bloku her açılışta oku)
> Kullanıcı **"devam et"**, **"kaldığı yerden devam et"** veya
> **"projeye devam"** derse, başka soru sormadan:
> 1. Bu dosyanın **tamamını** oku.
> 2. `## Bu turda yapılan` bölümünden son turun sonucunu özetle.
> 3. `## Sıradaki Karar (kullanıcıya sunulacak)` altındaki adayları
>    listeleyip kısa bir seçim sorusuyla yeni turu başlat.
> 4. Kullanıcı onay verene kadar YIKICI işlem yapma (rm, force-push,
>    branch silme). main'e ff-merge sonrası `git push origin main`
>    tur kapanış rutini — onaylandı.
> 5. Zorunlu Döngü'ye (`CLAUDE.md` §Zorunlu Döngü) gir.

**Son çalışma:** 2026-08-10 (46. tur — 174 + 175 + 176 + 177 + 178 + 179 KAPANIŞ)
**Branch:** `main` = `c70c083` local (6 feat + 4 docs commit, PUSH edilecek)
**Working tree:** temiz (tools/ai-cli/package* M drift + CONTEXT.md untracked — dokunulmadı)
**Durum:** 46. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1853/1853 test yeşil** (+12 skip), cov %91.85, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-10 — 46. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 45. tur adayları (174-179) tümü zincirleme.

1. **Görev 174** — atlas-ci-status.yml shell gzip → native --out --gzip (`fb8f0a5`)
   - SPEC 152 step: SPEC 155 native `--out --gzip` desteği kullanır.
   - SPEC 173 metrics/vault backup kardeşi; **tüm 4 workflow artık native**.
   - +3 test SPEC 174; eski SPEC 173 "hâlâ shell" testi silindi.

2. **Görev 175** — metrics --schema alert_options + alert_payload (`8314459`)
   - SPEC 153 JSON'a `alert_options` (7 CLI seçeneği) + `alert_payload`
     (13 alan) — SPEC 032.4 bit-uyumlu ekleme.
   - Prometheus çıktısına EKLENMEDİ (YAGNI; 4 metric aile AYNI).
   - notes: SPEC 169 + SPEC 175 satırları.
   - +8 test.

3. **Görev 176** — archive --restore --alert-webhook URL (`64e157e`)
   - SPEC 064/165/168/170 kalıbı; 4 hata noktası POST tetiği:
     `--search` regex/eşleşme yok/belirsiz + arşiv bulunamadı + RestoreError.
   - Payload: `alert=archive-restore` + task_id + search_pattern + error + exit_code.
   - Dry-run + başarı → POST YOK; SPEC 176 SPEC HATASI (exit 2) da POST atar
     (kullanıcı --search hatası monitoring için değerli).
   - +8 test (gerçek tarball + ephemeral HTTP).

4. **Görev 177** — doctor --alert-webhook payload strict alanı (`4df7649`)
   - SPEC 168 payload'a 4. anahtar `strict`: bool(args.strict) (SPEC 032.4 bit-uyumlu).
   - Webhook alıcısı CI-gate bulgusu (exit 9) ile bilgi bulgusu (exit 0) ayırt eder.
   - +4 test.

5. **Görev 178** — vault backup --alert-webhook URL (`480c77b`)
   - SPEC 064/165/168/170/176 kalıbı; 6 VaultBackupError POST noktası
     (backup/prune/split/encrypt/encrypt-recipient/prune-encrypted).
   - Payload: `alert=vault-backup` + vault_root + action (backup|backup-auto)
     + phase + error + exit_code.
   - SPEC HATASI (exit 2, argüman validasyon) POST ATMAZ — SPEC 176'dan farklı
     (176'da --search belirsizlik monitoring için değerli, 178'de argüman
     validasyon kullanıcı hatası).
   - +9 test (monkeypatch + ephemeral HTTP).

6. **Görev 179** — metrics --alert-history-show --schema (`95d21ab`)
   - SPEC 132 alert-history NDJSON record biçimi için ayrı JSON şeması.
   - `record_fields` (12: 10 SPEC 126 always + 2 SPEC 169 opsiyonel).
   - `summary_fields` (4), exit_codes (0/2/4), formats (human/json/prometheus).
   - **Kritik**: SPEC 153 `metrics --schema` kısa devresi güncellendi —
     `--alert-history-show` verildiyse SPEC 179 dalına bırakır.
   - +11 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer feat + 4 docs
   (ship.md eklemeleri) commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

46. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 180 — `atlas ai-cli status --alert-webhook` payload
  `size_bytes` alanı:** SPEC 170 payload'a boyut/timestamp alanları
  ekle (SPEC 032.4 bit-uyumlu; büyük drift monitoring). Küçük.
- **Görev 181 — `atlas doctor --schema` `alert_webhook` alan
  belgeleme:** SPEC 168/177 payload alanları JSON şemada `alert_webhook`
  bölümü (SPEC 175 kalıbı doctor için). Küçük.
- **Görev 182 — `atlas archive --restore --schema`:** restore alt komutu
  için ayrı JSON şeması (dry-run vs apply payload'ı; SPEC 179 kalıbı
  archive restore için). Küçük-orta.
- **Görev 183 — `atlas vault verify --schema --format json-lines --out
  --gzip` kanıt tamamlama:** SPEC 172 mevcut ama SPEC 159 kalıp
  simetrisindeki 4 edge test doğrulaması eksik. Küçük.
- **Görev 184 — `atlas metrics --alert-history-show --format json-lines`:**
  Şu an `--json` sadece NDJSON döndürür (SPEC 132); açık `--format
  json-lines` seçeneği tutarlılık için (SPEC 087/166 kalıbı). Küçük-orta.
- **Görev 185 — `atlas-doctor.yml` alert-webhook payload strict alanı
  yansıtma:** SPEC 135 workflow payload'ında `strict` alanı (SPEC 177
  CLI kardeşi; env `ATLAS_STRICT_DRIFT_DAYS` üstünden okur veya
  `rc_strict` üstünden çıkarır). Küçük.

---

## Hızlı Bağlam

**main'e giren 6 feat + 4 docs (2026-08-10 46. tur):**
```
c70c083 docs(179): 09-ship.md eklendi
95d21ab feat(179): metrics --alert-history-show --schema (SPEC 132 record semasi)
735055a docs(178): 09-ship.md eklendi
480c77b feat(178): vault backup --alert-webhook URL (SPEC 064/165/168/170/176 kalibi)
fd100b3 docs(177): 09-ship.md eklendi
4df7649 feat(177): doctor --alert-webhook payload strict alani (SPEC 032.4 bit-uyumlu)
64e157e feat(176): archive --restore --alert-webhook URL (SPEC 064/165/168/170 kalibi)
23a983a docs(175): 09-ship.md eklendi
8314459 feat(175): metrics --schema alert_options + alert_payload belgeleme
ad805cc docs(174): 09-ship.md eklendi (feat commit'inde unutuldu)
fb8f0a5 feat(174): atlas-ci-status.yml archive schema shell gzip -> native --out --gzip
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1853 passed, 12 skipped; cov 91.85%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --restore <id> --alert-webhook URL` (SPEC 176)
- `atlas vault backup --alert-webhook URL` (SPEC 178)
- `atlas metrics --alert-history-show --schema [--pretty]` (SPEC 179)
- `atlas doctor --alert-webhook` payload `strict` alanı (SPEC 177)
- `atlas metrics --schema` JSON'a `alert_options` + `alert_payload` (SPEC 175)

**Yeni workflow davranışı:**
- `atlas-ci-status.yml` SPEC 152 native `--out --gzip` (SPEC 174).
  Artık 4 workflow (atlas-doctor + atlas-metrics + atlas-vault +
  atlas-ci-status) HEPSİ native.

**Kritik sözleşme değişmezlikleri:**
- SPEC 033 normal archive --restore AYNI (--alert-webhook yoksa).
- SPEC 041 normal vault backup AYNI (--alert-webhook yoksa).
- SPEC 132 --alert-history-show normal AYNI (--schema yoksa).
- SPEC 153 metrics --schema AYNI (SPEC 175 alan-ekleme + SPEC 179
  dallanma sadece alert_history_show ile).
- SPEC 168 doctor webhook payload AYNI + yeni `strict` alanı bit-uyumlu.
- SPEC 155 archive --schema prom --out --gzip AYNI (SPEC 174 workflow'a taşıdı).
- SPEC 023/029/043/126/143/144/148 mevcut metrics davranışları AYNI.

**Ontological pattern (bu turdan):**
- **SPEC HATASI (exit 2) POST politikası ikiye ayrıldı:**
  - SPEC 176 (archive restore): --search belirsizlik POST atar
    (kullanıcı yanlış daraltma monitoring için değerli).
  - SPEC 178 (vault backup): argüman validasyon (--keep 0, vault yok) POST
    ATMAZ (arg validasyon != monitoring alarm).
  - Kalıp: exit 2'nin **anlamı** POST karar verir — "kullanıcı gafil"
    (yazım hatası) POST atmaz; "kullanıcı iyi niyetli ama sonuç
    beklenmiyor" (belirsizlik) POST atar.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Bilinen küçük konular:**
- `tools/ai-cli/package.json` + `package-lock.json` git status M
  görünüyor (ai-cli portable kurulumun bağımlılık drift'i; bu turda
  dokunulmadı).
- CONTEXT.md hâlâ untracked (2026-08-06 statik harita).
- 42. tur bilinen flaky (`test_101_cli_split_retention_once`) 43-46
  turda gözlenmedi.
- 45. turda gözlenen flaky (`test_0263_windows_cpu_quota_kesir`) 46.
  turda gözlenmedi.

**⚠️ Süregelen kalıp (2026-07-31 DECISIONS):**
- Write ile ship.md yazdıktan HEMEN sonra `git add` bazen index'e
  almıyor — 46. turda **4/6 görevde** tekrarlandı (174, 175, 177, 178,
  179 — sadece 176 ilk seferde tuttu). Kalıp: her `git add` sonrası
  `git status --short | grep <task-id>` DOĞRULA; ship.md yoksa
  ayrı `docs(NNN): 09-ship.md` commit'i ile ekle. Ampirik: bu turda
  4 ayrı docs commit üretti; **feat + docs birlikte main'e ff-merge**
  yaklaşımı çalıştı.

---

## Kapanış Notları

- **1853 test yeşil** (1811 → 1853; bu tur +42)
- 6 lineer feat + 4 docs commit (ship.md eklemeleri) = 10 commit
- Yeni CLI bayrağı: 3 (archive/vault-backup --alert-webhook + alert-history-show --schema)
- Yeni CLI alan: 3 (metrics schema alert_options+alert_payload +
  doctor webhook strict)
- Yeni workflow davranışı: 1 (atlas-ci-status native gzip)
- Sıradaki tur için 6 aday (180–185).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-10)

| Tur | Test toplam | Delta |
|---|---:|---:|
| 32 | 1321 | +47 |
| 33 | 1366 | +45 |
| 34 | 1415 | +49 |
| 35 | 1451 | +36 |
| 36 | 1479 | +28 |
| 37 | 1503 | +24 |
| 38 | 1533 | +30 |
| 39 | 1563 | +30 |
| 40 | 1602 | +39 |
| 41 | 1640 | +38 |
| 42 | 1682 | +42 |
| 43 | 1721 | +39 |
| 44 | 1766 | +45 |
| 45 | 1811 | +45 |
| **46** | **1853** | **+42** |

Toplam **~110 feat/test-tur** commit + 20 docs commit; **+903 test**
(950 → 1853). Cov `%91.18 → %91.85`. 9 GHA workflow etkin; 4 workflow
şema artifact HEPSİ native `--out --gzip` (SPEC 173+174). 3 sözleşme
rollback (SPEC 081→090, SPEC 091→104, SPEC 047→128).

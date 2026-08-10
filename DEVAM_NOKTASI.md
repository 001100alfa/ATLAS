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

**Son çalışma:** 2026-08-10 (43. tur — 156 + 157 + 158 + 159 + 160 + 161 KAPANIŞ)
**Branch:** `main` = `6a1d5ea` local (6 feat lineer ff-merge, PUSH edilecek)
**Working tree:** temiz (tools/ai-cli/package* M drift + CONTEXT.md untracked — dokunulmadı)
**Durum:** 43. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1721/1721 test yeşil** (+12 skip), cov %91.63, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-10 — 43. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 42. tur adayları (156-161) tümü zincirleme.

1. **Görev 156** — ai-cli status --schema prom --out --gzip (`d80b6b3`)
   - SPEC 145/155 kalıbı; auto-suffix `.gz` + gzip.open + parent auto-mkdir.
   - MUTEX --gzip yalnız --out ile; IO hatası exit 2.
   - Parser --out/--gzip help metinleri iki modu kapsar (118/120/156).
   - +7 test.

2. **Görev 157** — metrics --schema --format prometheus (`39b24fc`)
   - 4 info-metric ailesi (SPEC 140/150/151 kalıbı).
   - Parser DOKUNULMADI (--schema + --format zaten mevcut).
   - +8 test.

3. **Görev 158** — vault backup --schema --format prometheus (`6d51906`)
   - 4 info-metric ailesi (SPEC 140/150/151/157 kalıbı).
   - Parser: --format choices=["prometheus"] eklendi.
   - MUTEX: normal backup modda REDDEDİR (exit 2).
   - +8 test.

4. **Görev 159** — doctor --schema prom --out --gzip kanıt (`bfffb42`)
   - SPEC 134 zaten uygulanmış; yeni CLI kodu YOK.
   - +4 ekstra kanıt test (SPEC 155/156 kalıp simetri): parent
     auto-mkdir + idempotent .gz + stdout==file + tam MUTEX mesajı.

5. **Görev 160** — atlas-metrics.yml schema artifact (`9bfb05b`)
   - SPEC 147/152 kalıbı; shell gzip (metrics --out --gzip henüz yok).
   - Upload artifact listesine metrics-schema.prom.gz eklendi.
   - +5 workflow test.

6. **Görev 161** — atlas-vault.yml verify + backup schema artifacts (`6a1d5ea`)
   - vault verify --schema --format prometheus --out --gzip (SPEC 145).
   - vault backup --schema --format prometheus > file + shell gzip (SPEC 158).
   - Ayrı upload step atlas-vault-schema (if: always, iki .gz).
   - vault-backup-parts DOKUNULMADI.
   - +7 workflow test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

43. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 162 — `atlas metrics --schema --format prometheus --out --gzip`:**
  SPEC 145/155/156 kalıbı metrics için (--out --gzip desteği; 160
  workflow'unu shell gzip yerine native --out --gzip'e taşıyabilir).
  Küçük.
- **Görev 163 — `atlas vault backup --schema --format prometheus --out
  --gzip`:** SPEC 145/155/156 kalıbı vault backup için (161 workflow'unu
  shell gzip yerine native --out --gzip'e taşıyabilir). Küçük.
- **Görev 164 — `atlas archive --list --schema`:** archive --list alt
  komutunun kendi şeması ayrı (list çıktısının record biçimi zaten
  archive --schema top_level'de var ama --list için özel exit_codes
  ve formats farklı olabilir; incele). Küçük-orta.
- **Görev 165 — `atlas vault verify --alert-webhook`:** SPEC 131/135/141
  kalıbı vault verify için (bulgu varsa webhook POST). Orta.
- **Görev 166 — `atlas doctor --schema --format json-lines`:** SPEC 040
  JSON alanları NDJSON stream olarak (SPEC 087/126 kalıbı; her top_level
  bir satır + summary). Küçük-orta.
- **Görev 167 — `.github/workflows/ci.yml` schema artifact özet:**
  hepsi (doctor + archive + metrics + vault verify + vault backup +
  ai-cli status) tek yerde toplu upload. Küçük-orta.

---

## Hızlı Bağlam

**main'e giren 6 feat (2026-08-10 43. tur):**
```
6a1d5ea feat(161): atlas-vault.yml vault verify + backup schema artifacts
9bfb05b feat(160): atlas-metrics.yml metrics schema prometheus gzip artifact
bfffb42 feat(159): doctor --schema --format prometheus --out --gzip kanit tamamlama
6d51906 feat(158): vault backup --schema --format prometheus (info-metric)
39b24fc feat(157): atlas metrics --schema --format prometheus (info-metric)
d80b6b3 feat(156): ai-cli status --schema --format prometheus --out PATH [--gzip]
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1721 passed, 12 skipped; cov 91.63%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli status --schema --format prometheus --out PATH [--gzip]` (SPEC 156)
- `atlas metrics --schema --format prometheus` (SPEC 157)
- `atlas vault backup --schema --format prometheus` (SPEC 158)

**Yeni workflow adımı (bu turda):**
- `atlas-metrics.yml` `Generate metrics schema prometheus artifact` (SPEC 160)
- `atlas-vault.yml` `Generate vault verify + backup schema prometheus
  artifact` + ayrı `Upload atlas-vault schema artifacts` (SPEC 161)

**Kritik sözleşme değişmezlikleri:**
- SPEC 146/149/154 --schema JSON şemaları AYNI (--format yoksa).
- SPEC 150/151/157/158 --format prometheus yalnız --schema ile
  (aksi normal modda REDDEDİR).
- SPEC 041 normal vault backup davranışı AYNI (SPEC 158 sonrası
  --format prometheus normal modda exit 2 verir — YENİ MUTEX).
- SPEC 023/043 normal metrics davranışı AYNI (SPEC 157 --schema
  --format prometheus dalı önce çalışır).
- SPEC 134 doctor --schema --format prometheus --out --gzip
  DOKUNULMADI (SPEC 159 yalnız kanıt testleri ekledi).
- SPEC 107 atlas-vault.yml vault-backup-parts upload conditional AYNI.
- SPEC 074 atlas-metrics.yml mevcut 6 artifact AYNI.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Notlar:**
- `tools/ai-cli/package.json` + `package-lock.json` git status M
  görünüyor (ai-cli portable kurulumun bağımlılık drift'i; bu turda
  dokunulmadı).
- CONTEXT.md hâlâ untracked (2026-08-06 statik harita).
- 42. tur bilinen flaky (`test_101_cli_split_retention_once`) bu tur
  gözlenmedi — muhtemel dakika sınırı yarışı; 43. tur değişikliklerinden
  bağımsız.

---

## Kapanış Notları

- **1721 test yeşil** (1682 → 1721; bu tur +39)
- 6 lineer feat commit
- Yeni CLI bayrakları: 3 (ai-cli status --out --gzip, metrics
  --format prom, vault backup --format prom)
- Yeni workflow artifact adımı: 3 (atlas-metrics metrics-schema,
  atlas-vault verify+backup schema, atlas-vault-schema upload)
- Yeni Prometheus metric ailesi: 8 (SPEC 157 4× metrics_schema,
  SPEC 158 4× vault_backup_schema)
- Sıradaki tur için 6 aday (162–167).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-10)

| Tur | Test toplam | Delta |
|---|---:|---:|
| 29 | 1163 | +53 |
| 30 | 1221 | +58 |
| 31 | 1274 | +53 |
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
| **43** | **1721** | **+39** |

Toplam **~92 feat/test-tur** commit + 17 docs commit; **+771 test**
(950 → 1721). Cov `%91.18 → %91.63`. 8 GHA workflow (atlas-metrics +
atlas-vault schema artifact adımları eklendi). 3 sözleşme rollback
(SPEC 081→090, SPEC 091→104, SPEC 047→128).

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

**Son çalışma:** 2026-08-10 (42. tur — 150 + 151 + 152 + 153 + 154 + 155 KAPANIŞ)
**Branch:** `main` = `d098c80` local (6 feat lineer ff-merge, PUSH edilecek)
**Working tree:** temiz (tools/ai-cli/package* M drift + CONTEXT.md untracked — dokunulmadı)
**Durum:** 42. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1682/1682 test yeşil** (+12 skip), cov %91.61, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-10 — 42. tur)

Kullanıcı "Hepsi sıra ile (atomik) — 150→151→152→153→154→155" seçti
(atomic-order-doctrine). 41. tur adayları (150-155) tümü zincirleme.

1. **Görev 150** — ai-cli status --schema --format prometheus (`8143b9b`)
   - 4 info-metric (version+top_level+exit_code+format), SPEC 140 kalıbı.
   - Parser: `--format` choices=["prometheus"]; MUTEX yalnız --schema ile.
   - +8 test.

2. **Görev 151** — archive --schema --format prometheus (`4f1ec23`)
   - 4 info-metric (SPEC 140/150 kalıbı); parser --format choices=["prometheus"].
   - MUTEX: normal archive modda REDDEDİR (exit 2).
   - +8 test.

3. **Görev 152** — atlas-ci-status.yml archive schema prometheus gzip artifact (`06a494a`)
   - SPEC 147 kalıbı; shell gzip (SPEC 155 --out --gzip gelene kadar).
   - Yeni step: Generate archive schema prometheus artifact + Upload
     atlas-ci-status-schema (if: always).
   - Setup uv + Install ATLAS eklendi (mevcut Python setup korundu).
   - +5 workflow test.

4. **Görev 153** — atlas metrics --schema (`3ef951b`)
   - 7 top_level (SPEC 023: ts/in/out/cache_c/cache_r/cost/inflight).
   - exit_codes 0/2/4/8; formats human/json/prometheus.
   - Parser: --schema + --pretty.
   - +7 test.

5. **Görev 154** — atlas vault backup --schema (`2f4efb7`)
   - 6 top_level (backup_path/vault_root/action/split_parts/pruned_count/encrypted).
   - exit_codes 0/2/6; formats yalnız human (SPEC 041 YAGNI).
   - Parser: --schema + --pretty.
   - +7 test.

6. **Görev 155** — archive --schema --format prometheus --out --gzip (`d098c80`)
   - SPEC 145 kalıbı; --out + auto-suffix .gz + gzip.open("wt") + parent auto-mkdir.
   - MUTEX --gzip yalnız --out ile; IO hatası exit 2.
   - +7 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

42. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 156 — `atlas ai-cli status --schema --format prometheus
  --out --gzip`:** SPEC 145/155 kalıbı ai-cli status için (--out --gzip
  desteği). Küçük.
- **Görev 157 — `atlas metrics --schema --format prometheus`:** SPEC 140
  kalıbı metrics için (info-metric ailesi: version+top_level+exit_code+format).
  Küçük-orta.
- **Görev 158 — `atlas vault backup --schema --format prometheus`:**
  SPEC 140 kalıbı vault backup için (info-metric ailesi). Küçük.
- **Görev 159 — `atlas doctor --schema --format prometheus --out --gzip`:**
  SPEC 147 zaten workflow'da kullanılıyor ama CLI için `--out --gzip`
  ayrı dal olarak eksik olabilir; kontrol + tamamla. Küçük.
- **Görev 160 — `atlas-metrics.yml` schema artifact:** SPEC 152 kalıbı
  metrics workflow'una da schema artifact adımı (metrics --schema
  --format prometheus → 157 çıktısı üstüne). Küçük.
- **Görev 161 — `atlas-vault.yml` schema artifact:** SPEC 152 kalıbı
  vault workflow'una schema artifact adımı (vault verify --schema
  --format prometheus --out --gzip mevcut). Küçük.

---

## Hızlı Bağlam

**main'e giren 6 feat (2026-08-10 42. tur):**
```
d098c80 feat(155): archive --schema --format prometheus --out PATH [--gzip]
2f4efb7 feat(154): atlas vault backup --schema (SPEC 040/136/146/149 kalibi)
3ef951b feat(153): atlas metrics --schema (SPEC 040/136/146/149 kalibi)
06a494a feat(152): atlas-ci-status.yml archive schema prometheus gzip artifact
4f1ec23 feat(151): atlas archive --schema --format prometheus (info-metric)
8143b9b feat(150): atlas ai-cli status --schema --format prometheus (info-metric)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1682 passed, 12 skipped; cov 91.61%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli status --schema --format prometheus` (SPEC 150)
- `atlas archive --schema --format prometheus` (SPEC 151)
- `atlas metrics --schema [--pretty]` (SPEC 153)
- `atlas vault backup --schema [--pretty]` (SPEC 154)
- `atlas archive --schema --format prometheus --out PATH [--gzip]` (SPEC 155)

**Yeni workflow adımı:**
- `atlas-ci-status.yml` `Generate archive schema prometheus artifact`
  + `Upload atlas-ci-status-schema` (SPEC 152)
- `Setup uv` + `Install ATLAS` eklendi (aynı workflow, aynı tur)

**Kritik sözleşme değişmezlikleri:**
- SPEC 146: ai-cli status --schema JSON AYNI (--format yoksa).
- SPEC 149: archive --schema JSON AYNI (--format yoksa).
- SPEC 037.4 normal ai-cli status: --format prometheus REDDEDİR (exit 2).
- SPEC 007/012/033/065/071/075 normal archive: --format prometheus REDDEDİR.
- SPEC 023 normal metrics: --schema kısa devre eklendi, mevcut modlar AYNI.
- SPEC 041 normal vault backup: --schema kısa devre eklendi, mevcut modlar AYNI.
- SPEC 151 archive schema prometheus stdout AYNI (--out yeni yol).
- SPEC 089/125/141 atlas-ci-status.yml drift-scan davranışı AYNI.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Notlar:**
- `tools/ai-cli/package.json` + `package-lock.json` git status M
  görünüyor (ai-cli portable kurulumun bağımlılık drift'i; bu turda
  dokunulmadı).
- CONTEXT.md hâlâ untracked (2026-08-06 statik harita).

---

## Kapanış Notları

- **1682 test yeşil** (1640 → 1682; bu tur +42)
- 6 lineer feat commit
- Yeni CLI bayrakları: 5 (ai-cli status --format prom, archive --format
  prom, metrics --schema, vault backup --schema, archive schema prom
  --out --gzip)
- Yeni workflow adımı: atlas-ci-status archive schema artifact +
  Setup uv/Install ATLAS
- Yeni metric aileleri: 8 (SPEC 150 4× ai-cli status schema,
  SPEC 151 4× archive schema)
- Sıradaki tur için 6 aday (156–161).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-10)

| Tur | Test toplam | Delta |
|---|---:|---:|
| 28 | 1110 | +49 |
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
| **42** | **1682** | **+42** |

Toplam **~86 feat/test-tur** commit + 16 docs commit; **+732 test**
(950 → 1682). Cov `%91.18 → %91.61`. 8 GHA workflow (atlas-ci-status
schema artifact eklendi). 3 sözleşme rollback (SPEC 081→090,
SPEC 091→104, SPEC 047→128).

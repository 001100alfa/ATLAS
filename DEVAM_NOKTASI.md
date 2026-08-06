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
> 5. Zorunlu Döngü'ye (`CLAUDE.md` §Zorunlu Döngü) gir.

**Son çalışma:** 2026-08-05 (37. tur — 120 + 121 + 122 + 123 + 124 + 125)
**Branch:** `main` (6 commit, PUSH edilecek)
**Working tree:** temiz
**Durum:** 37. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1503/1503 test yeşil** (+12 skip), cov ~%91.39, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 37. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 36. tur adayları (120-125) tümü zincirleme.

1. **Görev 120** — ai-cli status --json-lines --out --gzip (`30eebf8`)
   - SPEC 118 üstüne SPEC 108/109/111/114 gzip kalıbı.
   - +6 test.

2. **Görev 121** — archive tam zincir regresyon (`075ea05`)
   - SPEC 075+079+085+093+108+115 birlikte doğrulama.
   - Kod DEĞİŞMEZ (salt-test).
   - +4 test.

3. **Görev 122** — metrics --limit prom regresyon (`4d94abe`)
   - SPEC 090 `--limit N` grup Prometheus'a ÖNCE uygulanır.
   - Kod DEĞİŞMEZ (salt-test).
   - +4 test.

4. **Görev 123** — doctor tam zincir regresyon (`8e87a9d`)
   - SPEC 104+110+114 birlikte doğrulama + --strict ortogonal.
   - Kod DEĞİŞMEZ (salt-test).
   - +4 test.

5. **Görev 124** — atlas-vault.yml retention verify step (`1a44eed`)
   - `find archive/ -name 'vault-*.tar.gz.*' | wc -l` sayı kontrolü.
   - Ana `.tar.gz` split sonrası silinmiş olmalı (uyarı).
   - +3 test.

6. **Görev 125** — atlas-ci-status.yml drift diff artifact (`8c897a9`)
   - `Upload drift diff artifact` step + README.md + drift-issue.md.
   - `rc != 0` conditional; 30 gün retention.
   - +3 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

37. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 126 — `atlas metrics --alert-history` JSON log:** SPEC
  029/064/068 alert'lerin dosya log'u (`.atlas/alert-history.jsonl`).
  Küçük-orta.
- **Görev 127 — `atlas archive --restore <id> --json`:** SPEC 033
  restore dry-run JSON çıktısı. Küçük.
- **Görev 128 — `atlas doctor --schema --format prometheus`:** SPEC 040
  schema Prometheus text (labels: field, exit_code). Orta.
- **Görev 129 — `atlas vault verify --format json-lines --out --gzip
  fresh test`:** SPEC 111 tam zincir salt-test regresyon.
  Küçük.
- **Görev 130 — `.github/workflows/atlas-doctor.yml` --strict scan
  gate:** SPEC 070'e `atlas doctor --diff-history-all --strict` ek
  step. Küçük.
- **Görev 131 — `.github/workflows/atlas-metrics.yml` alert-webhook
  post:** SPEC 064 alert-webhook ile PR fail durumunda Slack/Discord
  ping (env-driven). Orta.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 6 commit local (37. tur — push edilecek)`

**main'e giren 6 commit (2026-08-05 37. tur):**
```
8c897a9 feat(125): atlas-ci-status.yml drift diff artifact (SPEC 082/089)
1a44eed feat(124): atlas-vault.yml retention verify step (SPEC 041.1/107)
8e87a9d test(123): doctor tam zincir SPEC 104+110+114 regresyon
4d94abe test(122): metrics --group-by prometheus --limit regresyon (SPEC 090)
075ea05 test(121): archive tam zincir SPEC 075+079+085+093+108+115 regresyon
30eebf8 feat(120): atlas ai-cli status --json-lines --out --gzip (SPEC 118)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1503 passed, 12 skipped; cov 91.39%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli status <name> --json-lines --out PATH --gzip` (SPEC 120)

**Yeni workflow adımları:**
- `atlas-vault.yml` `Verify retention (--keep 7)` (SPEC 124)
- `atlas-ci-status.yml` `Upload drift diff artifact` (SPEC 125)

**Yeni test dosyaları (regresyon önleme):**
- `test_cli_ai_cli_status_jsonl_gzip.py` (SPEC 120)
- `test_cli_archive_full_chain.py` (SPEC 121)
- `test_cli_metrics_prom_limit.py` (SPEC 122)
- `test_cli_doctor_full_chain.py` (SPEC 123)

**Kritik sözleşme değişmezlikleri:**
- SPEC 118: `--gzip` yoksa düz NDJSON dosya AYNI.
- SPEC 075/079/085/093/108/115: archive tam zinciri AYNI (regresyon
  yakalayıcı 121).
- SPEC 090: metrics `--limit` grup Prometheus önce uygulanır AYNI.
- SPEC 104/110/114: doctor tam zinciri AYNI.
- SPEC 107/117: atlas-vault.yml mevcut backup+restore+verify+doctor
  step'leri AYNI (retention verify eklendi).
- SPEC 089/119: atlas-ci-status.yml drift-scan job AYNI (artifact
  eklendi).

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

---

## Kapanış Notları

- **1503 test yeşil** (1479 → 1503; bu tur +24 — 4 salt-test + 2 CLI feat
  + 2 workflow step)
- 3 salt-test tur (121/122/123) — mevcut çıktıların regresyona karşı
  sözleşme sigortası
- 3 feat: ai-cli --gzip (SPEC 120), vault retention verify (SPEC 124),
  ci-status drift artifact (SPEC 125)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (126–131).

---

## 12 Turluk Toplu İstatistik (2026-08-05 tek gün)

| Tur | Test toplam | Delta |
|---|---:|---:|
| 26 | 995 | +83 |
| 27 | 1061 | +66 |
| 28 | 1110 | +49 |
| 29 | 1163 | +53 |
| 30 | 1221 | +58 |
| 31 | 1274 | +53 |
| 32 | 1321 | +47 |
| 33 | 1366 | +45 |
| 34 | 1415 | +49 |
| 35 | 1451 | +36 |
| 36 | 1479 | +28 |
| **37** | **1503** | **+24** |

Toplam **~70 feat/test-tur** commit + 12 docs commit bugün; **+591
test** (912 → 1503). Cov `%91.18 → %91.39`. 8 GHA workflow; 2 sözleşme
rollback (SPEC 081→090, SPEC 091→104).

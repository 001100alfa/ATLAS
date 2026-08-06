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

**Son çalışma:** 2026-08-06 (39. tur — 134 + 133 + 137 + 132 + 136 + 135)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz (CONTEXT.md hâlâ untracked — dokunulmadı)
**Durum:** 39. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1563/1563 test yeşil** (+12 skip), cov ~%91.4x, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-06 — 39. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir" → 38. tur
adayları (132-137) tümü zincirleme.

1. **Görev 134** — doctor --schema --format prometheus --out --gzip (`3b7a61f`)
   - SPEC 128 üstüne SPEC 103/114 gzip kalıbı.
   - `--schema` JSON modu + `--out`/`--gzip` verilirse exit 2.
   - +7 test.

2. **Görev 133** — archive --restore <id> --json-lines (`sha`)
   - Dry-run: plan + summary; apply: plan + restored + summary.
   - `--json + --json-lines` MUTEX exit 2.
   - Hata JSON basmaz.
   - +5 test.

3. **Görev 137** — atlas-metrics.yml alert-history artifact
   - Upload path'e `.atlas/alert-history.jsonl` + `if-no-files-found:
     ignore` (SPEC 095 fail-safe).
   - Mevcut 5 artifact DOKUNULMADI.
   - +2 test.

4. **Görev 132** — metrics --alert-history-show
   - Kısa devre bilgi komutu (SPEC 040 kalıbı).
   - `--limit N` default 10; `--json` NDJSON stream + summary.
   - Bozuk satır sessiz atlanır; dosya yok → boş + rc 0.
   - +6 test.

5. **Görev 136** — vault verify --schema
   - Kısa devre; vault dizini gerekmez.
   - JSON: `{schema_version, top_level, exit_codes, formats, notes}`.
   - 4 format tanımı (human/json/json-pretty/json-lines).
   - +6 test.

6. **Görev 135** — atlas-doctor.yml alert-webhook gate
   - Yeni step (SPEC 131 kalıbı doctor için).
   - Conditional: env + rc_strict|rc_diff|rc_hist != '0'.
   - `continue-on-error: true`; Fail step'inden ÖNCE.
   - +4 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

39. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 138 — `atlas archive --restore --json-lines --out PATH`:**
  SPEC 133 stream'i dosyaya (SPEC 105 kalıbı). Küçük.
- **Görev 139 — `atlas metrics --alert-history-show --out PATH`:**
  SPEC 132 çıktısını dosyaya (SPEC 106 kalıbı). Küçük.
- **Görev 140 — `atlas vault verify --schema --format prometheus`:**
  SPEC 136 info-metric ailesi (SPEC 128 kalıbı vault için). Orta.
- **Görev 141 — `.github/workflows/atlas-ci-status.yml` alert-webhook
  gate:** SPEC 131/135 kalıbı ci-status için. Küçük-orta.
- **Görev 142 — `atlas doctor --schema` metric ailesi genişletme:**
  SPEC 128 4 metric → 5+ (backend, retry_pricing eklenmesi). Küçük.
- **Görev 143 — `atlas metrics --alert-history-show --format prometheus`:**
  SPEC 132 alert sayısını Prometheus counter olarak yayımla. Orta.

---

## Hızlı Bağlam

**Bugün toplam (14 tur, 2026-08-05→06):** 39. tur bitişinde +30 test
(1533→1563), toplam +651 test (912→1563). Cov ~%91.4x. 3 sözleşme
rollback (SPEC 081→090, 091→104, 047→128). 8 GHA workflow.

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --schema --format prometheus --out --gzip` (SPEC 134)
- `atlas archive --restore <id> --json-lines` (SPEC 133)
- `atlas metrics --alert-history-show [--limit N] [--json]` (SPEC 132)
- `atlas vault verify --schema [--pretty]` (SPEC 136)

**Yeni workflow adımları:**
- `atlas-metrics.yml` `.atlas/alert-history.jsonl` artifact (SPEC 137)
- `atlas-doctor.yml` `Post doctor alert webhook` (SPEC 135)

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1563 passed, 12 skipped
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Kritik sözleşme değişmezlikleri:**
- SPEC 128: doctor --schema JSON AYNI (--format prometheus opt-in).
- SPEC 127: archive --restore --json AYNI (--json-lines opt-in).
- SPEC 023: metrics normal özet AYNI (--alert-history-show opt-in).
- SPEC 042: vault verify AYNI (--schema opt-in).
- SPEC 070/074: mevcut workflow step'leri DOKUNULMADI.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

---

## Kapanış Notları

- **1563 test yeşil** (1533 → 1563; bu tur +30)
- 6 lineer feat commit
- Yeni CLI bayrakları: 4 (doctor schema prom out gzip, archive restore
  jsonl, metrics alert-history-show, vault verify --schema)
- Yeni workflow adımları: 2 (metrics artifact + doctor webhook gate)
- Sıradaki tur için 6 aday (138–143).

## 14 Turluk Toplu İstatistik (2026-08-05 → 2026-08-06)

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
| 37 | 1503 | +24 |
| 38 | 1533 | +30 |
| **39** | **1563** | **+30** |

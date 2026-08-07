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

**Son çalışma:** 2026-08-06 (40. tur — 139 + 138 + 141 + 143 + 142 + 140)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz (CONTEXT.md untracked, dokunulmadı; tools/ai-cli
lock unrelated M)
**Durum:** 40. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1602/1602 test yeşil** (+12 skip), cov ~%91.44, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-06 — 40. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 39. tur adayları (138-143) tümü zincirleme.

1. **Görev 139** — metrics --alert-history-show --json --out PATH (`32a14fe`)
   - `--out` yalnız `--json` ile; parent auto-mkdir; IO exit 2.
   - Dosya içeriği stdout `--json` modu ile BİT-UYUMLU.
   - +6 test.

2. **Görev 138** — archive --restore <id> --json-lines --out PATH (`473e5bc`)
   - `_restore_emit_lines(records)` helper (stdout|PATH DRY).
   - Hata → dosya YAZILMAZ (early return).
   - +8 test.

3. **Görev 141** — atlas-ci-status.yml alert-webhook gate (`6fe1e78`)
   - SPEC 131/135 kalıp simetrik.
   - Env `ALERT_WEBHOOK_URL`; payload `{alert:"ci-status", rc, run_id, sha, event}`.
   - `continue-on-error: true`.
   - +4 test.

4. **Görev 143** — metrics --alert-history-show --format prometheus (`77061e9`)
   - 3 counter metric: `history_total`, `history_recent`, `channel_total`.
   - Kanallar alfabetik lex; boş `channels=[]` → `channel="-"` bucket.
   - +7 test.

5. **Görev 142** — doctor --schema metric ailesi genişletme (`614d562`)
   - `_doctor_schema_descriptor()` 3 yeni alan (backend_options +
     retry_pricing_envs + storage_envs).
   - 2 yeni Prometheus metric (backend_option + env).
   - Toplam metric ailesi 4 → 6 (BİT-UYUMLU ekleme).
   - +6 yeni + 1 test update (SPEC 128 sayı 4→6).

6. **Görev 140** — vault verify --schema --format prometheus (`3c508e1`)
   - Parser `--format` choices'a `prometheus` eklendi.
   - Semantik MUTEX: yalnız `--schema` ile (aksi exit 2).
   - 4 info-metric ailesi: version + top_level + exit_code + format.
   - `schema: dict[str, Any]` (mypy narrow).
   - +8 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

40. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 144 — `atlas metrics --alert-history-show --format prometheus
  --out PATH`:** SPEC 143 stream'i dosyaya (SPEC 096 kalıbı). Küçük.
- **Görev 145 — `atlas vault verify --schema --format prometheus --out`:**
  SPEC 140 dosyaya (SPEC 134 kalıbı). Küçük.
- **Görev 146 — `atlas ai-cli status --schema`:** SPEC 040/136 kalıbı
  ai-cli için (JSON şema tanımı). Küçük.
- **Görev 147 — `.github/workflows/atlas-doctor.yml` schema artifact:**
  `atlas doctor --schema --format prometheus > doctor-schema.prom.gz`
  → upload. Küçük.
- **Görev 148 — `atlas metrics --alert-history-show --strict`:** log
  var mı yok mu → strict + exit 4 (SPEC 094 kalıbı). Küçük-orta.
- **Görev 149 — `atlas archive --schema`:** SPEC 136 kalıbı archive
  --list şema tanımı (fields + exit codes + formats). Küçük.

---

## Hızlı Bağlam

**main'e giren 6 feat (2026-08-06 40. tur):**
```
3c508e1 feat(140): atlas vault verify --schema --format prometheus (info-metric)
614d562 feat(142): doctor --schema metric ailesi genisletme (SPEC 128 uzerine)
77061e9 feat(143): atlas metrics --alert-history-show --format prometheus
6fe1e78 feat(141): atlas-ci-status.yml alert-webhook gate (SPEC 131/135 kalibi)
473e5bc feat(138): atlas archive --restore <id> --json-lines --out PATH
32a14fe feat(139): atlas metrics --alert-history-show --json --out PATH
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1602 passed, 12 skipped; cov 91.44%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --restore <id> --json-lines --out PATH` (SPEC 138)
- `atlas metrics --alert-history-show --json --out PATH` (SPEC 139)
- `atlas metrics --alert-history-show --format prometheus` (SPEC 143)
- `atlas doctor --schema` 3 yeni alan + 2 yeni Prometheus metric (SPEC 142)
- `atlas vault verify --schema --format prometheus` (SPEC 140)

**Yeni workflow adımı:**
- `atlas-ci-status.yml` `Post ci-status alert webhook` (SPEC 141)

**Kritik sözleşme değişmezlikleri:**
- SPEC 133: archive --restore --json-lines stdout AYNI (--out yeni yol).
- SPEC 132: metrics --alert-history-show stdout AYNI (--out/--format yeni).
- SPEC 128: doctor --schema JSON şeması AYNI (yeni alan eklendi;
  SPEC 032.4 alan-ekleme kuralı = bit-uyumlu).
- SPEC 136: vault verify --schema JSON AYNI (--format prometheus yeni).
- SPEC 087: vault verify normal --format seçenekleri AYNI (`prometheus`
  yalnız --schema modu; normal modda exit 2).

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Notlar:**
- `tools/ai-cli/package.json` + `package-lock.json` git status M
  görünüyor (ai-cli portable kurulumun bağımlılık drift'i; bu turda
  dokunulmadı).
- CONTEXT.md hâlâ untracked (2026-08-06 statik harita).

---

## Kapanış Notları

- **1602 test yeşil** (1563 → 1602; bu tur +39)
- 6 lineer feat commit
- Yeni CLI bayrakları: 4 (archive --restore --out, metrics
  --alert-history-show --out, --format prometheus, vault verify
  --schema --format prometheus)
- Yeni workflow adımı: atlas-ci-status alert-webhook
- Yeni metric aileleri: 5 (SPEC 142 backend_option+env, SPEC 143
  history_total+recent+channel_total, SPEC 140 4× vault_verify_schema)
- Sıradaki tur için 6 aday (144–149).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-06)

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
| 39 | 1563 | +30 |
| **40** | **1602** | **+39** |

Toplam **~80 feat/test-tur** commit + 15 docs commit; **+690 test**
(912 → 1602). Cov `%91.18 → %91.44`. 8 GHA workflow; 3 sözleşme
rollback (SPEC 081→090, SPEC 091→104, SPEC 047→128).

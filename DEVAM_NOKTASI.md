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

**Son çalışma:** 2026-08-05 (35. tur — 108 + 109 + 110 + 111 + 112 + 113)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 35. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1451/1451 test yeşil** (+12 skip), cov ~%91.40, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 35. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 34. tur adayları (108-113) tümü zincirleme,
küçükten büyüğe.

1. **Görev 108** — archive --list --json-lines --out --gzip (`2e9cedd`)
   - `--gzip` yalnız `--out` ile; auto-suffix `.gz`.
   - gzip.open("wt") NDJSON stream (decompress BİT-UYUMLU).
   - +7 test.

2. **Görev 109** — ai-cli list --outdated --json-lines --out --gzip (`a14ebcc`)
   - `_pkg_line(p)` yardımcı lambda (DRY: düz + gzip aynı üretici).
   - `--strict` ile ORTOGONAL (exit 4 korunur, gzip'e yazılır).
   - +6 test.

3. **Görev 110** — doctor --diff-history-all --format prometheus --out PATH (`a4655e9`)
   - `--out` yalnız `--diff-history-all + --format prometheus` ile.
   - Dosya içeriği stdout modu ile BİT-UYUMLU.
   - `--strict` (SPEC 097) ORTOGONAL, exit 9 dosya yazıldıktan sonra.
   - +8 test.

4. **Görev 111** — vault verify --format json-lines --out --gzip (`e0cc8ed`)
   - `out_fh: Any` union tip (gzip TextIO vs Path.open TextIO).
   - `_emit` lambda değişmedi (her iki tip için write çalışır).
   - +7 test.

5. **Görev 112** — atlas-vault.yml restore-verify integrity step (`9eb5670`)
   - Backup sonrası: split .001'den restore → verify --strict.
   - Herhangi biri fail → workflow fail (`set -e`).
   - `/tmp/verify-vault` hedef (üretim'i bozmaz, idempotent).
   - +4 test.

6. **Görev 113** — atlas-metrics.yml grup prometheus gzip artifact (`ff sha`)
   - `atlas metrics --group-by day --format prometheus --gzip` →
     `metrics-group-day.prom.gz`.
   - Upload artifact listesine EKLENDİ; mevcut 4 artifact korundu.
   - +4 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

35. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 114 — `atlas doctor --diff-history-all --format prometheus
  --out --gzip`:** SPEC 110 çıktısını gzip (SPEC 103/108/109/111 kalıp).
  Küçük.
- **Görev 115 — `atlas archive --list --json`da `--out PATH`:** SPEC 105
  json-lines out'a paralel, ana JSON dizisini dosyaya. Küçük.
- **Görev 116 — `atlas metrics --group-by --with-cost --format
  prometheus`:** SPEC 084 cost_usd + SPEC 090 grup Prometheus fresh
  test (regresyon önleme; tek testte tam zincir). Küçük.
- **Görev 117 — `.github/workflows/atlas-vault.yml` `--strict` gate:**
  SPEC 112 restore-verify çıkışını doctor gate ile bağla. Küçük-orta.
- **Görev 118 — `atlas ai-cli status <name> --json-lines --out`:**
  SPEC 037.4 status'u JSON stream + dosya. Küçük.
- **Görev 119 — `.github/workflows/atlas-ci-status.yml` badge freshness
  weekly + PR annotation:** SPEC 089 daily + haftalık toplu inceleme.
  Küçük-orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 6 commit local (35. tur — push edilecek)`

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1451 passed, 12 skipped; cov 91.40%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --list --json-lines --out --gzip` (SPEC 108)
- `atlas ai-cli list --outdated --json-lines --out --gzip` (SPEC 109)
- `atlas doctor --diff-history-all --format prometheus --out PATH` (SPEC 110)
- `atlas vault verify --format json-lines --out --gzip` (SPEC 111)

**Yeni workflow adımları:**
- `atlas-vault.yml` `Restore + verify (integrity check)` (SPEC 112)
- `atlas-metrics.yml` `Generate group prometheus (gzip)` (SPEC 113)

**Yeni env sözleşmesi:** DEĞİŞMEDİ.

**Yeni yardımcılar:** yok (mevcut helper + inline dallar).

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri:**
- SPEC 105/106/092/104: `--gzip` yoksa davranış AYNI (BİT-UYUMLU).
- SPEC 041/101/102: mevcut backup/restore/split akışları AYNI.
- SPEC 074/084/095: atlas-metrics.yml mevcut 4 artifact + PR comment
  AYNI (yeni artifact upload path'ine EKLENDİ).
- SPEC 041.1/107: atlas-vault.yml backup step DOKUNULMADI (restore-
  verify AYNI job'a step olarak eklendi).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 6 blok (35/34/33/32/31/30. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1451 test yeşil** (1415 → 1451; bu tur +36; oturum başı 319'dan +1132)
- 6 lineer feat + docs commit
- Yeni CLI bayrakları: 4 (archive --gzip, ai-cli --gzip, doctor --out,
  vault verify --gzip)
- Yeni workflow adımları: 2 (atlas-vault restore+verify, atlas-metrics
  group prometheus gzip)
- Yeni test dosyaları:
  `test_cli_archive_jsonl_gzip.py`,
  `test_cli_ai_cli_jsonl_gzip.py`,
  `test_cli_doctor_diff_history_all_prom_out.py`,
  `test_cli_vault_verify_jsonl_gzip.py`,
  + `test_github_workflows.py` SPEC 112 + 113 blokları (4 dosya + 1 update, +36 test)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (114–119).

---

## 10 Turluk Toplu İstatistik (2026-08-05 tek gün)

| Tur | Bitiş commit | Test toplam | Delta | Yeni bayrak/komut |
|---|---|---:|---:|---|
| 26 | 03dec44 | 995 | +83 | doctor --diff, --http-check, vault fix-broken, replay --serve, metrics --alert-email, GHA vault-health |
| 27 | c086a78 | 1061 | +66 | ai-cli install, doctor --auto-baseline, vault backup --encrypt, metrics --alert-webhook, archive --search, JSON Schema doc |
| 28 | 32f6fdd | 1110 | +49 | metrics --alert-slack, vault backup --keep-encrypted, vault restore --decrypt, archive --restore --search, run --estimate, GHA atlas-doctor |
| 29 | dcc7f08 | 1163 | +53 | Docker YASAK gate (v5), atlas-metrics.yml, metrics --window, archive --list, --estimate --adaptive, vault backup --recipient |
| 30 | e2261f6 | 1221 | +58 | ci-status.yml, archive --list --sort-by, ai-cli uninstall, vault restore --decrypt-recipient, doctor --history, metrics --group-by |
| 31 | 232d85b | 1274 | +53 | archive --list --limit N, ai-cli list --outdated, atlas-ci-status.yml, vault verify --format json-lines, metrics --group-by --with-cost, doctor --diff-history N |
| 32 | 41a3506 | 1321 | +47 | vault verify --out PATH, ai-cli --outdated --strict, archive --list --name-match, atlas-metrics.yml cost artifact, doctor --diff-history-all, metrics group-by prometheus (SPEC 081 rollback) |
| 33 | ff828a5 | 1366 | +45 | ai-cli --json-lines, archive --list --json-lines, metrics prometheus --out, doctor --diff-history-all --strict, atlas-doctor.yml diff-history-all, vault backup --split SIZE_MB |
| 34 | 200e068 | 1415 | +49 | archive --json-lines --out, ai-cli --json-lines --out, metrics prometheus --gzip, doctor diff-history-all prometheus (SPEC 091 rollback), vault restore --split, atlas-vault.yml scheduled backup |
| **35** | **push** | **1451** | **+36** | archive --json-lines --gzip, ai-cli --json-lines --gzip, doctor prometheus --out PATH, vault verify --gzip, atlas-vault.yml restore+verify integrity, atlas-metrics.yml group prometheus gzip artifact |

Toplam **60 feat commit** + 10 docs commit bugün; **+539 test** (912
→ 1451). Cov `%91.18 → %91.40`. Docker YASAK otomatik gate; 8 GHA
workflow; 2 sözleşme rollback (SPEC 081 → 090, SPEC 091 → 104);
+44 CLI bayrak varyasyonu bu 10 turda.

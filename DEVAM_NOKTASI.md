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

**Son çalışma:** 2026-08-05 (34. tur — 105 + 106 + 103 + 104 + 102 + 107)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 34. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1415/1415 test yeşil** (+12 skip), cov ~%91.37, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 34. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir" → 33. tur
adayları (102-107) tümü zincirleme, küçükten büyüğe.

1. **Görev 105** — archive --list --json-lines --out PATH (`3c98d03`)
   - `--out` yalnız `--json-lines` ile; SPEC 092/096 kalıbı.
   - Parent auto-mkdir; IO hatası exit 2.
   - Dosya içeriği stdout modu ile BİT-UYUMLU.
   - +8 test.

2. **Görev 106** — ai-cli list --outdated --json-lines --out PATH (`6a014f1`)
   - SPEC 099 stream'i dosyaya (SPEC 105 kalıbı).
   - `--strict` ile ORTOGONAL (exit 4 korunur).
   - +7 test.

3. **Görev 103** — metrics --group-by prometheus --out --gzip (`e250a9c`)
   - `--gzip` yalnız `--out` ile; auto-suffix `.gz` ekle.
   - Decompress → düz metin BİT-UYUMLU (magic 1f 8b doğrulama).
   - Değişken adı `prom_text` (mypy no-redef kalıbı).
   - +7 test.

4. **Görev 104** — doctor --diff-history-all --format prometheus (`b7c5835`)
   - **SPEC 091 MUTEX KALDIRILDI** (2. rollback; SPEC 090 kalıbı).
   - 5 metric (3 counter + 2 gauge); labels `snapshot_date`.
   - `--strict` ile ORTOGONAL (SPEC 097 exit 9 korunur).
   - +8 yeni test + 1 test güncelleme.

5. **Görev 102** — vault restore <first.001> --split (`aaf2b7c`)
   - `combine_split_parts(first_part)` yeni yardımcı.
   - `.001` başlar, `.NNN` sıralı; parçalar KORUNUR.
   - `--decrypt`/`--decrypt-recipient` MUTEX (SPEC 101 simetrisi).
   - +11 test.

6. **Görev 107** — atlas-vault.yml scheduled backup + split (`b9c6c32`)
   - Yeni workflow: cron `0 3 * * *` + workflow_dispatch.
   - `atlas vault backup --auto --split 50 --keep 7`.
   - `has_vault` conditional (fail-safe).
   - +8 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

34. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 108 — `atlas archive --list --json-lines --out --gzip`:**
  SPEC 105 çıktısını gzip sıkıştırma (SPEC 103 kalıbı). Küçük.
- **Görev 109 — `atlas ai-cli list --outdated --json-lines --out --gzip`:**
  SPEC 106 çıktısını gzip. Küçük.
- **Görev 110 — `atlas doctor --diff-history-all --format prometheus
  --out PATH`:** SPEC 104 çıktısını dosyaya (SPEC 096 kalıbı). Küçük.
- **Görev 111 — `atlas vault verify --format json-lines --out --gzip`:**
  SPEC 092 çıktısını gzip. Küçük.
- **Görev 112 — `.github/workflows/atlas-vault.yml` restore-verify
  step:** SPEC 107 workflow'a "restore + verify integrity" adım ekle
  (backup sonrası tazelik kontrolü). Orta.
- **Görev 113 — `atlas metrics --group-by --format prometheus --out
  --gzip` + SPEC 095 workflow entegrasyonu:** atlas-metrics.yml'a
  gzip artifact eklenir. Küçük-orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 6 commit local (34. tur — push edilecek)`

**main'e giren 6 feat (2026-08-05 34. tur):**
```
b9c6c32 feat(107): atlas-vault.yml scheduled backup + split (SPEC 041/101)
aaf2b7c feat(102): atlas vault restore <first.001> --split (SPEC 101 birlestir)
b7c5835 feat(104): atlas doctor --diff-history-all --format prometheus (per-snapshot)
e250a9c feat(103): atlas metrics --group-by prometheus --out --gzip
6a014f1 feat(106): atlas ai-cli list --outdated --json-lines --out PATH
3c98d03 feat(105): atlas archive --list --json-lines --out PATH (SPEC 098 -> dosya)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1415 passed, 12 skipped; cov 91.37%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --list --json-lines --out PATH` (SPEC 105)
- `atlas ai-cli list --outdated --json-lines --out PATH` (SPEC 106)
- `atlas metrics --group-by --format prometheus --out --gzip` (SPEC 103)
- `atlas doctor --diff-history-all --format prometheus` (SPEC 104)
- `atlas vault restore <first.001> --split` (SPEC 102)

**Yeni workflow:** `.github/workflows/atlas-vault.yml` (scheduled daily
03:00 UTC, SPEC 107).

**Yeni env sözleşmesi:** DEĞİŞMEDİ.

**Yeni yardımcılar:** `combine_split_parts` (vault_backup.py, SPEC 102).

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri:**
- SPEC 098/099: `--out` yoksa stdout stream AYNI.
- SPEC 096: `--gzip` yoksa düz metin AYNI.
- SPEC 090: stdout Prometheus grup metrikleri AYNI (--out ile birlikte
  dosyaya yazılır, çıktı içerik AYNI).
- SPEC 091: pretty tablo + JSON şeması AYNI (--format prometheus yoksa).
- SPEC 041/066/078: mevcut restore/decrypt akışları AYNI.
- SPEC 101: `split_backup` DOKUNULMADI.

**Sözleşme değişikliği (rollback):**
- **SPEC 091 `--format prometheus` MUTEX KALDIRILDI** (SPEC 104).
  2. rollback (ilk SPEC 081 → SPEC 090). Kalıp: MUTEX geri alınabilir
  eğer yeni kullanım case'i doğal ihtiyaç ise.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 5 blok (34/33/32/31/30. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1415 test yeşil** (1366 → 1415; bu tur +49; oturum başı 319'dan +1096)
- 6 lineer feat + docs commit
- Yeni CLI bayrakları: 4 (archive --json-lines --out, ai-cli
  --json-lines --out, metrics --gzip, vault restore --split)
- 1 yeni Prometheus metric ailesi (doctor_history_*, SPEC 104)
- 1 yeni yardımcı fonksiyon: `combine_split_parts`
- 1 sözleşme değişikliği (2. rollback): SPEC 091 MUTEX kaldırıldı (104)
- Yeni workflow: `atlas-vault.yml` (cron 03:00 UTC, SPEC 107)
- Yeni test dosyaları:
  `test_cli_archive_jsonl_out.py`,
  `test_cli_ai_cli_jsonl_out.py`,
  `test_cli_metrics_prom_gzip.py`,
  `test_cli_doctor_diff_history_all_prom.py`,
  `test_cli_vault_restore_split.py`,
  + `test_github_workflows.py` SPEC 107 bölümü (5 dosya + 1 update, +49 test)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (108–113).

---

## 9 Turluk Toplu İstatistik (2026-08-05 tek gün)

| Tur | Bitiş commit | Test toplam | Delta | Yeni bayrak/komut |
|---|---|---:|---:|---|
| 26 | 03dec44 | 995 | +83 | doctor --diff, --http-check, vault fix-broken, replay --serve, metrics --alert-email, GHA vault-health |
| 27 | c086a78 | 1061 | +66 | ai-cli install, doctor --auto-baseline, vault backup --encrypt, metrics --alert-webhook, archive --search, JSON Schema doc |
| 28 | 32f6fdd | 1110 | +49 | metrics --alert-slack, vault backup --keep-encrypted, vault restore --decrypt, archive --restore --search, run --estimate, GHA atlas-doctor |
| 29 | dcc7f08 | 1163 | +53 | Docker YASAK gate (v5), atlas-metrics.yml, metrics --window, archive --list, --estimate --adaptive, vault backup --recipient |
| 30 | e2261f6 | 1221 | +58 | ci-status.yml, archive --list --sort-by, ai-cli uninstall, vault restore --decrypt-recipient, doctor --history, metrics --group-by |
| 31 | 232d85b | 1274 | +53 | archive --list --limit N, ai-cli list --outdated, atlas-ci-status.yml, vault verify --format json-lines, metrics --group-by --with-cost, doctor --diff-history N |
| 32 | 41a3506 | 1321 | +47 | vault verify --out PATH, ai-cli list --outdated --strict, archive --list --name-match, atlas-metrics.yml cost artifact, doctor --diff-history-all, metrics group-by prometheus (SPEC 081 rollback) |
| 33 | ff828a5 | 1366 | +45 | ai-cli list --json-lines, archive --list --json-lines, metrics prometheus --out, doctor --diff-history-all --strict, atlas-doctor.yml diff-history-all, vault backup --split SIZE_MB |
| **34** | **push** | **1415** | **+49** | archive --json-lines --out, ai-cli --json-lines --out, metrics prometheus --gzip, doctor diff-history-all prometheus (SPEC 091 rollback), vault restore --split, atlas-vault.yml scheduled backup |

Toplam **54 feat commit** + 9 docs commit bugün; **+503 test** (912
→ 1415). Cov `%91.18 → %91.37`. Docker YASAK otomatik gate; 8 GHA
workflow (vault-health, atlas-doctor, atlas-metrics, no-docker,
ci-status, atlas-ci-status, atlas-vault, + ci); 2 sözleşme rollback
(SPEC 081 → 090, SPEC 091 → 104); +40 CLI bayrak varyasyonu bu 9 turda.

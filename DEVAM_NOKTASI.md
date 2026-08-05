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

**Son çalışma:** 2026-08-05 (32. tur — 092 + 094 + 093 + 095 + 091 + 090)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 32. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1321/1321 test yeşil** (+12 skip), cov ~%91.44, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 32. tur)

Kullanıcı "devam et → hepsini sıra ile uygula" → 31. tur adayları
(090-095) tümü zincirleme, küçükten büyüğe.

1. **Görev 092** — vault verify --format json-lines --out PATH (`cc95edb`)
   - `--out PATH` stdout yerine NDJSON dosyaya stream (büyük vault).
   - Yalnız `--format json-lines` ile anlamlı → aksi exit 2.
   - Parent auto-mkdir; try/finally close; yazma hatası exit 2.
   - `--strict` / `--dump-report` ORTOGONAL.
   - +10 test.

2. **Görev 094** — ai-cli list --outdated --strict (`a711dac`)
   - `--strict` yalnız `--outdated` ile anlamlı.
   - Bulgu varsa exit 4 (SPEC 042 kalıbı); "SAĞLIK BAŞARISIZ" stderr.
   - `--strict` yoksa SPEC 088 BİT-UYUMLU.
   - +6 test.

3. **Görev 093** — archive --list --name-match PATTERN (`d962b95`)
   - `--name-match PATTERN` regex arşiv adı filtresi.
   - Filtre sort ÖNCE (list → filter → sort → limit).
   - `--search` (içerik) ile ORTOGONAL.
   - Boş sonuç ayrımı: `(esleme yok)` / `(arsiv yok)`.
   - +8 test.

4. **Görev 095** — atlas-metrics.yml --with-cost artifact (`4e02aeb`)
   - Yeni step: `Generate cost by day (SPEC 084/095)`.
   - Upload artifact listesi + `metrics-cost-by-day.json`.
   - Env fiyat yoksa cost 0 (fail-safe); `||` fallback workflow durmaz.
   - +4 test (SPEC 095 bloğu `test_github_workflows.py`).

5. **Görev 091** — doctor --diff-history-all (`b0329de`)
   - Tüm tarihçe ile mevcut toplu diff (date desc tablo).
   - `--json` snapshots listesi (SPEC 057 delta şeması).
   - MUTEX: `--diff/--auto-baseline/--diff-history/--save-baseline/
     --serve/--format prometheus`. `--schema` BİT-UYUMLU (kısa devre).
   - Bozuk snapshot best-effort continue + UYARI.
   - +10 test.

6. **Görev 090** — metrics --group-by --format prometheus (`7ff06fc`)
   - **SPEC 081 MUTEX (`--group-by + --format prometheus`) KALDIRILDI**.
   - 5 base grup metric + opsiyonel `cost_usd` (`--with-cost` ile).
   - Labels: `unit`, `key` (Prometheus text v0.0.4 escape).
   - `--group-by + --alert` MUTEX KORUNDU.
   - +9 yeni test + 1 test güncelleme (eski MUTEX → yeni davranış).

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

32. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 096 — `atlas metrics --group-by --format prometheus --out PATH`:**
  SPEC 090 grup Prometheus çıktısı dosyaya (SPEC 092 kalıbı). CI'de
  scrape endpoint yerine artifact. Küçük.
- **Görev 097 — `atlas doctor --diff-history-all --strict`:** SPEC 091
  toplu diff + herhangi bir snapshot'ta regresyon → exit 9 (SPEC 032
  kalıbı). Küçük-orta.
- **Görev 098 — `atlas archive --list --name-match --json-lines`:**
  SPEC 093 filtre + streaming NDJSON (büyük arşiv sayısı). Küçük.
- **Görev 099 — `atlas ai-cli list --outdated --json-lines`:** SPEC 088
  filtre + NDJSON (CI parse kolay). Küçük.
- **Görev 100 — `.github/workflows/atlas-doctor.yml` --diff-history-all
  entegrasyonu:** SPEC 070 doctor workflow'a toplu diff artifact
  eklenir. Küçük-orta.
- **Görev 101 — `atlas vault backup --split SIZE_MB`:** SPEC 041 backup
  büyük vault'lar için parçalı tar (multi-volume). Orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 6 commit local (32. tur — push edilecek)`

**main'e giren 6 feat (2026-08-05 32. tur):**
```
7ff06fc feat(090): atlas metrics --group-by --format prometheus (grup histogram)
b0329de feat(091): atlas doctor --diff-history-all (SPEC 086 toplu diff)
4e02aeb feat(095): atlas-metrics.yml --with-cost entegrasyonu (yeni artifact)
d962b95 feat(093): atlas archive --list --name-match PATTERN (regex ad filtresi)
a711dac feat(094): atlas ai-cli list --outdated --strict (CI/pre-commit uyumlu)
cc95edb feat(092): atlas vault verify --format json-lines --out PATH
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1321 passed, 12 skipped; cov 91.44%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas vault verify --format json-lines --out PATH` (SPEC 092)
- `atlas ai-cli list --outdated --strict` (SPEC 094)
- `atlas archive --list --name-match PATTERN` (SPEC 093)
- `atlas doctor --diff-history-all` (SPEC 091)
- `atlas metrics --group-by --format prometheus [--with-cost]` (SPEC 090)

**Yeni workflow adımı:** `atlas-metrics.yml` `Generate cost by day` +
`metrics-cost-by-day.json` artifact (SPEC 095).

**Yeni env sözleşmesi:** DEĞİŞMEDİ.

**Yeni yardımcılar:** yok (mevcut helpers yeniden kullanıldı).

**Exit kodları:**
- ai-cli list --outdated --strict + bulgu → **exit 4** (yeni; SPEC 094).

**Kritik sözleşme değişmezlikleri:**
- SPEC 087: vault verify `--out` yoksa stdout stream AYNI.
- SPEC 088: `--strict` yoksa exit 0 AYNI.
- SPEC 075/079/085: archive `--name-match` yoksa davranış AYNI.
- SPEC 074: atlas-metrics.yml mevcut 3 artifact üretimi + PR comment
  AYNI (yeni artifact upload path'e EKLENDİ).
- SPEC 086: doctor `--diff-history N` davranışı AYNI.
- SPEC 043: metrics `--format prometheus` tekil metrikler AYNI
  (--group-by yoksa).

**Sözleşme değişikliği (rollback):**
- **SPEC 081 `--group-by + --format prometheus` MUTEX KALDIRILDI**
  (SPEC 090). Karar geri alındı: cost eklendikten sonra grup histogram
  gerçek ihtiyaç oldu. `--group-by + --alert` MUTEX KORUNDU.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 3 blok (32/31/30. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1321 test yeşil** (1274 → 1321; bu tur +47; oturum başı 319'dan +1002)
- 6 lineer feat + docs commit
- Yeni CLI bayrakları: 4 (vault verify --out, ai-cli list --strict,
  archive --list --name-match, doctor --diff-history-all)
- Yeni Prometheus grup metric ailesi: 5 base + 1 opsiyonel cost_usd
- 1 sözleşme değişikliği: SPEC 081 MUTEX kaldırıldı (090)
- Yeni test dosyaları:
  `test_cli_vault_verify_jsonl_out.py`,
  `test_cli_ai_cli_outdated_strict.py`,
  `test_cli_archive_list_name_match.py`,
  `test_cli_doctor_diff_history_all.py`,
  `test_cli_metrics_group_by_prometheus.py`,
  + `test_github_workflows.py` SPEC 095 bloğu (5 dosya + 1 update, +47 test)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (096–101).

---

## 7 Turluk Toplu İstatistik (2026-08-05 tek gün)

| Tur | Bitiş commit | Test toplam | Delta | Yeni bayrak/komut |
|---|---|---:|---:|---|
| 26 | 03dec44 | 995 | +83 | doctor --diff, --http-check, vault fix-broken, replay --serve, metrics --alert-email, GHA vault-health |
| 27 | c086a78 | 1061 | +66 | ai-cli install, doctor --auto-baseline, vault backup --encrypt, metrics --alert-webhook, archive --search, JSON Schema doc |
| 28 | 32f6fdd | 1110 | +49 | metrics --alert-slack, vault backup --keep-encrypted, vault restore --decrypt, archive --restore --search, run --estimate, GHA atlas-doctor |
| 29 | dcc7f08 | 1163 | +53 | Docker YASAK gate (v5), atlas-metrics.yml, metrics --window, archive --list, --estimate --adaptive, vault backup --recipient |
| 30 | e2261f6 | 1221 | +58 | ci-status.yml, archive --list --sort-by, ai-cli uninstall, vault restore --decrypt-recipient, doctor --history, metrics --group-by |
| 31 | 232d85b | 1274 | +53 | archive --list --limit N, ai-cli list --outdated, atlas-ci-status.yml (daily cron), vault verify --format json-lines, metrics --group-by --with-cost, doctor --diff-history N |
| **32** | **push** | **1321** | **+47** | vault verify --out PATH, ai-cli list --outdated --strict, archive --list --name-match PATTERN, atlas-metrics.yml cost artifact, doctor --diff-history-all, metrics --group-by --format prometheus (MUTEX rollback) |

Toplam **42 feat commit** + 7 docs commit bugün; **+409 test** (912
→ 1321). Cov `%91.18 → %91.44`. Docker YASAK otomatik gate; 7 GHA
workflow; **1 sözleşme rollback** (SPEC 081 → SPEC 090); +30 CLI
bayrak varyasyonu bu 7 turda.

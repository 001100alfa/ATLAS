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

**Son çalışma:** 2026-08-05 (31. tur — 085 + 088 + 089 + 087 + 084 + 086)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 31. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1274/1274 test yeşil** (+12 skip), cov ~%91.43+, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 31. tur)

Kullanıcı "devam et → hepsini sıra ile uygula" → 30. tur adayları
(084-089) tümü zincirleme, küçükten büyüğe.

1. **Görev 085** — archive --list --limit N (`3ea8974`)
   - `--limit N` sıralamadan SONRA `entries[:N]` (top-N).
   - `N<=0` → SPEC HATASI exit 2; `N>len` → tüm liste.
   - `--limit` YOKSA SPEC 075/079 BİT-UYUMLU.
   - +8 test.

2. **Görev 088** — ai-cli list --outdated (`950e7fb`)
   - `_strip_semver_prefix`: `^`, `~`, `>=`, `>`, `=`, `*`, boşluk.
   - Filter: `installed is None` VEYA `stripped != installed`.
   - Pretty başlık suffix `— outdated`, boş → `(guncelleme yok)`.
   - +8 test.

3. **Görev 089** — atlas-ci-status.yml scheduled daily (`9d30f57`)
   - Yeni workflow: cron `0 6 * * *` + workflow_dispatch.
   - Drift → `peter-evans/create-issue-from-file@v5` issue.
   - README badge tablosu regen (SPEC 082 gate).
   - +7 test.

4. **Görev 087** — vault verify --format json-lines (`6733c33`)
   - `--format {human,json,json-pretty,json-lines}` yeni bayrak.
   - `--format` + `--json`/`--pretty` MUTEX exit 2.
   - NDJSON: bulgu başına 1 satır + son satır summary.
   - +10 test.

5. **Görev 084** — metrics --group-by --with-cost (`d2cc451`)
   - `_group_cost_usd(g, Pin, Pout)` — SPEC 043 formülü AYNI (DRY).
   - `--with-cost` yalnız `--group-by` ile; env yok → cost 0 + UYARI.
   - +10 test.

6. **Görev 086** — doctor --diff-history N (`e8ba243`)
   - `_list_doctor_history()` date desc → N=1 en yeni.
   - `--diff/--auto-baseline/--save-baseline` MUTEX.
   - SPEC 057 delta şeması BİT-UYUMLU.
   - +10 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

31. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 090 — `atlas metrics --group-by --with-cost --format prometheus`:**
  Şu an SPEC 081 `--group-by + --format prometheus` MUTEX (exit 2).
  SPEC 084 cost eklendikten sonra prometheus'a grup histogramı olarak
  açılabilir (labels: `key`, `unit`). Orta.
- **Görev 091 — `atlas doctor --diff-history --all`:** SPEC 086 tek
  snapshot; `--all` tüm tarihçeyi mevcuta karşı toplu diff (tablo).
  Orta.
- **Görev 092 — `atlas vault verify --format json-lines --dump PATH`:**
  SPEC 087 stream'i doğrudan dosyaya (stdout değil). Küçük.
- **Görev 093 — `atlas archive --list --search PATTERN`:** SPEC 065
  arama + SPEC 075 liste birleşimi (arşiv adı regex filtresi). Küçük-orta.
- **Görev 094 — `atlas ai-cli list --outdated --strict`:** SPEC 088
  filtre + boş değilse exit 4 (CI/pre-commit uyumlu). Küçük.
- **Görev 095 — `.github/workflows/atlas-metrics.yml` --with-cost
  entegrasyonu:** SPEC 074 metrics workflow'una `--with-cost` bayrağı
  ekle + prometheus/json artifact. Küçük-orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 6 commit local (31. tur — push edilecek)`

**main'e giren 6 feat (2026-08-05 31. tur):**
```
e8ba243 feat(086): atlas doctor --diff-history N (SPEC 080 tarihce delta)
d2cc451 feat(084): atlas metrics --group-by --with-cost (SPEC 081 uzerine cost_usd)
6733c33 feat(087): atlas vault verify --format json-lines (streaming NDJSON)
9d30f57 feat(089): atlas-ci-status.yml scheduled daily drift scan
950e7fb feat(088): atlas ai-cli list --outdated (SPEC 037.2 uzerine filtre)
3ea8974 feat(085): atlas archive --list --limit N (SPEC 079 uzerine top-N)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1274 passed, 12 skipped; cov 91.43%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --list --limit N` (SPEC 079 üstüne top-N)
- `atlas ai-cli list --outdated`
- `atlas vault verify --format {human,json,json-pretty,json-lines}`
- `atlas metrics --group-by KEY --with-cost`
- `atlas doctor --diff-history N`

**Yeni workflow:** `.github/workflows/atlas-ci-status.yml` (scheduled daily).

**Yeni env sözleşmesi:** DEĞİŞMEDİ.

**Yeni yardımcılar:**
- `_strip_semver_prefix` (cli.py, SPEC 088)
- `_group_cost_usd` (cli.py, SPEC 084)

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri:**
- SPEC 075/079 archive `--list` default `name` + tam liste BİT-UYUMLU
  (SPEC 085 `--limit` opsiyonel).
- SPEC 037.2 ai-cli list tam liste BİT-UYUMLU (SPEC 088 `--outdated`
  opsiyonel).
- SPEC 042 vault verify mevcut `--json`/`--pretty` yolu BİT-UYUMLU
  (SPEC 087 `--format` yeni yol, MUTEX).
- SPEC 081 metrics `--group-by` grup dict alanları BİT-UYUMLU (SPEC 084
  `--with-cost` yalnız cost_usd EKLER).
- SPEC 057 doctor `--diff` delta şeması BİT-UYUMLU (SPEC 086 sadece
  farklı kaynak).
- SPEC 082 ci-status.yml push/PR gate DOKUNULMADI (SPEC 089 AYRI cron).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 2 blok (31/30. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1274 test yeşil** (1221 → 1274; bu tur +53; oturum başı 319'dan +955)
- 6 lineer feat + docs commit
- Yeni CLI bayrakları: 5 (archive --list --limit, ai-cli list
  --outdated, vault verify --format, metrics --group-by --with-cost,
  doctor --diff-history)
- Yeni workflow: `atlas-ci-status.yml` (cron 06:00 UTC)
- Yeni yardımcı fonksiyonlar: 2 (cli.py)
- Yeni test dosyaları: `test_cli_archive_list_limit.py`,
  `test_cli_ai_cli_list_outdated.py`,
  `test_cli_vault_verify_jsonl.py`,
  `test_cli_metrics_with_cost.py`,
  `test_cli_doctor_diff_history.py`,
  + `test_github_workflows.py` SPEC 089 bölümü (6 dosya, +53 test)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (090–095).

---

## 6 Turluk Toplu İstatistik (2026-08-05 tek gün)

| Tur | Bitiş commit | Test toplam | Delta | Yeni bayrak/komut |
|---|---|---:|---:|---|
| 26 | 03dec44 | 995 | +83 | doctor --diff, --http-check, vault fix-broken, replay --serve, metrics --alert-email, GHA vault-health |
| 27 | c086a78 | 1061 | +66 | ai-cli install, doctor --auto-baseline, vault backup --encrypt, metrics --alert-webhook, archive --search, JSON Schema doc |
| 28 | 32f6fdd | 1110 | +49 | metrics --alert-slack, vault backup --keep-encrypted, vault restore --decrypt, archive --restore --search, run --estimate, GHA atlas-doctor |
| 29 | dcc7f08 | 1163 | +53 | Docker YASAK gate (v5), atlas-metrics.yml, metrics --window, archive --list, --estimate --adaptive, vault backup --recipient |
| 30 | e2261f6 | 1221 | +58 | ci-status.yml, archive --list --sort-by, ai-cli uninstall, vault restore --decrypt-recipient, doctor --history, metrics --group-by |
| **31** | **push** | **1274** | **+53** | archive --list --limit N, ai-cli list --outdated, atlas-ci-status.yml (daily cron), vault verify --format json-lines, metrics --group-by --with-cost, doctor --diff-history |

Toplam **36 feat commit** + 6 docs commit bugün; **+362 test** (912
→ 1274). Cov `%91.18 → %91.43`. Docker YASAK otomatik gate; 7 GHA
workflow (vault-health, atlas-doctor, atlas-metrics, no-docker,
ci-status, atlas-ci-status, + ci); 5 yeni CLI komutu/bayrak varyasyonu
bu turda.

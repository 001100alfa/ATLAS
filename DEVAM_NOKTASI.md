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

**Son çalışma:** 2026-08-10 (44. tur — 162 + 163 + 164 + 165 + 166 + 167 KAPANIŞ)
**Branch:** `main` = `7c176e9` local (6 feat lineer ff-merge, PUSH edilecek)
**Working tree:** temiz (tools/ai-cli/package* M drift + CONTEXT.md untracked — dokunulmadı)
**Durum:** 44. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1766/1766 test yeşil** (+12 skip), cov %91.61, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-10 — 44. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 43. tur adayları (162-167) tümü zincirleme.

1. **Görev 162** — metrics --schema prom --out --gzip (`6bda8f2`)
   - SPEC 145/155/156 kalıbı; auto-suffix + gzip.open + parent auto-mkdir.
   - Parser --out/--gzip help metinleri iki modu kapsar (096/103/162).
   - +7 test.

2. **Görev 163** — vault backup --schema prom --out --gzip (`fdb85e9`)
   - SPEC 145/155/156/162 kalıbı; auto-suffix + gzip.open.
   - Parser: `--gzip` yeni argüman; `--out` help iki mod kapsıyor.
   - YENİ MUTEX: normal backup modda `--gzip` verilirse SPEC HATASI exit 2.
   - +8 test.

3. **Görev 164** — archive --schema sub_commands + --list --schema (`0d84502`)
   - JSON'a `sub_commands` alanı (SPEC 032.4 bit-uyumlu):
     list=0/2 restore=0/2/3/6 search=0/2 all=0/2.
   - archive --list --schema mevcut şema ile birebir (kısa devre).
   - Prometheus çıktısına EKLENMEDİ (YAGNI; 4 metric aile AYNI).
   - +8 test.

4. **Görev 165** — vault verify --alert-webhook URL (`815a6d4`)
   - SPEC 064 metrics kalıbı; bulgu (is_clean False) varsa POST.
   - `_post_alert_webhook()` yeniden kullanıldı (stdlib urllib).
   - Payload: alert=vault-verify + vault_root + counts.
   - Başarısız POST → stderr uyarı; exit code KORUR.
   - --strict ile ORTOGONAL.
   - +6 test (ephemeral HTTP server).

5. **Görev 166** — doctor --schema --format json-lines (`faa397e`)
   - SPEC 087/126 NDJSON stream (top_level/quality_field/backend_option/
     env/exit_code) + son satır summary.
   - --out PATH [--gzip] destek (SPEC 145/155/156/162 kalıbı).
   - SPEC 134 MUTEX genişletildi: "prometheus VEYA json-lines".
   - YENİ MUTEX: json-lines yalnız --schema ile (normal modda reddet).
   - Parser: --format choices'a json-lines eklendi.
   - +9 test.

6. **Görev 167** — ci.yml schema-artifacts özet job (`7c176e9`)
   - Yeni job schema-artifacts (ubuntu-latest); mevcut quality +
     test-windows DOKUNULMADI.
   - 6 schema komutu native --out --gzip (shell gzip YOK):
     doctor + archive + metrics + vault verify + vault backup + ai-cli status.
   - Tek upload `atlas-schema-artifacts` (6 .gz, if: always).
   - +7 workflow test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

44. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 168 — `atlas doctor --alert-webhook URL`:** SPEC 165 kalıbı
  doctor için (quality.* uyarı sayısı > 0 ise POST). Küçük.
- **Görev 169 — `atlas metrics --alert-webhook` genişletme:** mevcut
  SPEC 064 tek uyarı (cache-hit) yerine `--alert-window MINUTES` gibi
  ek eşik/yeni payload alanları. Küçük-orta.
- **Görev 170 — `atlas ai-cli status --alert-webhook URL`:** SPEC 165/168
  kalıbı ai-cli status için (--strict + up_to_date=False ise POST).
  Küçük.
- **Görev 171 — `atlas archive --schema --format json-lines`:** SPEC 166
  kalıbı archive schema için (NDJSON stream). Küçük.
- **Görev 172 — `atlas vault verify --schema --format json-lines`:**
  SPEC 166 kalıbı vault verify schema için (NDJSON stream). Küçük.
- **Görev 173 — `atlas-metrics.yml/atlas-vault.yml` schema artifact
  taşıma:** SPEC 160/161 shell gzip → native --out --gzip'e taşı
  (SPEC 162/163 sayesinde artık native destek var). Küçük.

---

## Hızlı Bağlam

**main'e giren 6 feat (2026-08-10 44. tur):**
```
7c176e9 feat(167): ci.yml schema-artifacts ozet job (6 schema tek artifact)
faa397e feat(166): doctor --schema --format json-lines NDJSON stream
815a6d4 feat(165): atlas vault verify --alert-webhook URL (SPEC 064 kalibi)
0d84502 feat(164): archive --schema sub_commands alani; --list --schema bit-uyumlu
fdb85e9 feat(163): vault backup --schema --format prometheus --out PATH [--gzip]
6bda8f2 feat(162): metrics --schema --format prometheus --out PATH [--gzip]
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1766 passed, 12 skipped; cov 91.61%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas metrics --schema --format prometheus --out PATH [--gzip]` (SPEC 162)
- `atlas vault backup --schema --format prometheus --out PATH [--gzip]` (SPEC 163)
- `atlas archive --schema` JSON'da `sub_commands` alanı (SPEC 164)
- `atlas vault verify --alert-webhook URL` (SPEC 165)
- `atlas doctor --schema --format json-lines [--out PATH [--gzip]]` (SPEC 166)

**Yeni workflow adımı (bu turda):**
- `ci.yml` yeni job `schema-artifacts` — 6 schema tek yerde
  `atlas-schema-artifacts` artifact (SPEC 167)

**Kritik sözleşme değişmezlikleri:**
- SPEC 157 metrics stdout prom AYNI (--out yoksa).
- SPEC 158 vault backup stdout prom AYNI (--out yoksa).
- SPEC 149 archive JSON şema geriye uyumlu (sub_commands yeni alan;
  Prometheus çıktısı 4 metric aile AYNI — sub_commands yok).
- SPEC 042 normal vault verify AYNI (--alert-webhook yoksa).
- SPEC 040 doctor JSON default AYNI (--format yoksa).
- SPEC 128 doctor Prometheus AYNI (yeni json-lines dalı ayrı).
- SPEC 041 normal vault backup + SPEC 041.1/041.2/101 argümanları AYNI.
- SPEC 147/152/160/161 mevcut workflow schema artifact adımları AKTİF
  (ci.yml yeni job paralel).

**YENİ MUTEX'ler (bu turda):**
- vault backup normal modda `--gzip` verilirse SPEC HATASI (SPEC 163).
- doctor normal modda `--format json-lines` verilirse SPEC HATASI (SPEC 166).

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Notlar:**
- `tools/ai-cli/package.json` + `package-lock.json` git status M
  görünüyor (ai-cli portable kurulumun bağımlılık drift'i; bu turda
  dokunulmadı).
- CONTEXT.md hâlâ untracked (2026-08-06 statik harita).
- 42. tur bilinen flaky (`test_101_cli_split_retention_once`) 43. ve
  44. turda gözlenmedi.

---

## Kapanış Notları

- **1766 test yeşil** (1721 → 1766; bu tur +45)
- 6 lineer feat commit
- Yeni CLI bayrağı: 5 (metrics --out --gzip, vault backup --out --gzip,
  archive sub_commands, vault verify --alert-webhook, doctor --format
  json-lines --out --gzip)
- Yeni workflow job: 1 (ci.yml schema-artifacts, 6 schema toplu upload)
- Yeni MUTEX: 2 (vault backup normal modda --gzip, doctor normal modda
  --format json-lines)
- Sıradaki tur için 6 aday (168–173).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-10)

| Tur | Test toplam | Delta |
|---|---:|---:|
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
| 43 | 1721 | +39 |
| **44** | **1766** | **+45** |

Toplam **~98 feat/test-tur** commit + 18 docs commit; **+816 test**
(950 → 1766). Cov `%91.18 → %91.61`. 9 GHA workflow etkin (ci.yml
schema-artifacts job eklendi; 8 mevcut). 3 sözleşme rollback
(SPEC 081→090, SPEC 091→104, SPEC 047→128).

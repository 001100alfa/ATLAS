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

**Son çalışma:** 2026-08-05 (36. tur — 114 + 116 + 115 + 118 + 117 + 119)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 36. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1479/1479 test yeşil** (+12 skip), cov ~%91.37, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 36. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 35. tur adayları (114-119) tümü zincirleme.

1. **Görev 114** — doctor prometheus --out --gzip (`07ae709`)
   - SPEC 110 üstüne SPEC 103/108/109/111 gzip kalıbı.
   - +6 test.

2. **Görev 116** — metrics tam zincir regresyon testleri (`7034225`)
   - SPEC 084+090+096+103 birlikte → dosya+gzip+cost_usd.
   - Kod DEĞİŞMEZ (salt-test tur).
   - +4 test.

3. **Görev 115** — archive --list --json --out PATH (`f44f3e4`)
   - `--out` mutex genişletildi (--json VEYA --json-lines).
   - --gzip ile ORTOGONAL.
   - SPEC 105 test güncellendi (eski mutex → yeni davranış).
   - +7 test + 1 update.

4. **Görev 118** — ai-cli status <name> --json-lines --out (`35ea75e`)
   - 8 alan satırı + summary NDJSON.
   - --json + --json-lines MUTEX; --out yalnız --json-lines ile.
   - +6 test.

5. **Görev 117** — atlas-vault.yml doctor gate (`0e600e8`)
   - Restore edilen vault üzerinde `atlas doctor --strict --scan-src`.
   - ATLAS_VAULT=/tmp/verify-vault env override.
   - +4 test.

6. **Görev 119** — atlas-ci-status.yml weekly cron (`98c017b`)
   - `0 7 * * 1` (Pazartesi 07:00 UTC) eklendi; daily korundu.
   - +1 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

36. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 120 — `atlas ai-cli status <name> --json-lines --out --gzip`:**
  SPEC 118 stream'i gzip (SPEC 108/109/111 kalıbı). Küçük.
- **Görev 121 — `atlas archive --list --json --out --gzip fresh test`:**
  SPEC 115 tam zincir regresyon. Küçük.
- **Görev 122 — `atlas metrics --group-by --format prometheus --limit N`
  fresh test:** SPEC 090 --limit ile birlikte grup hesaplama regresyon.
  Küçük.
- **Görev 123 — `atlas doctor --diff-history-all --format prometheus
  --out --gzip fresh test`:** SPEC 114 tam zincir regresyon. Küçük.
- **Görev 124 — `.github/workflows/atlas-vault.yml` retention verify
  step:** SPEC 041.1 `--keep 7` retention'ın gerçekten uygulandığı
  kontrol. Küçük-orta.
- **Görev 125 — `.github/workflows/atlas-ci-status.yml` --diff-only
  komut çıktısı diff artifact:** SPEC 082 gen_ci_badges.py `--check`
  farkını dosyaya yaz + upload. Küçük.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**main'e giren 6 feat (2026-08-05 36. tur):**
```
98c017b feat(119): atlas-ci-status.yml weekly cron (SPEC 089 uzerine)
0e600e8 feat(117): atlas-vault.yml doctor gate on restored vault
35ea75e feat(118): atlas ai-cli status <name> --json-lines --out PATH
f44f3e4 feat(115): atlas archive --list --json --out PATH (SPEC 075 -> dosya)
7034225 test(116): metrics tam zincir SPEC 084+090+096+103 regresyon
07ae709 feat(114): atlas doctor prometheus --out --gzip (SPEC 110 uzerine)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1479 passed, 12 skipped; cov 91.37%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --diff-history-all --format prometheus --out --gzip` (SPEC 114)
- `atlas archive --list --json --out PATH [--gzip]` (SPEC 115)
- `atlas ai-cli status <name> --json-lines [--out PATH]` (SPEC 118)

**Yeni workflow adımları:**
- `atlas-vault.yml` `Doctor gate on restored vault` (SPEC 117)
- `atlas-ci-status.yml` haftalık cron `0 7 * * 1` (SPEC 119)

**Kritik sözleşme değişmezlikleri:**
- SPEC 110/075/037.4/089/112: mevcut davranışlar AYNI.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

---

## 11 Turluk Toplu İstatistik (2026-08-05 tek gün)

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
| **36** | **1479** | **+28** |

Toplam **65 feat + 1 test-tur** + 11 docs commit bugün; **+567 test**
(912 → 1479). Cov `%91.18 → %91.37`. 8 GHA workflow; 2 sözleşme
rollback; +48 CLI bayrak varyasyonu.

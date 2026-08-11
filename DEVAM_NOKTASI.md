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

**Son çalışma:** 2026-08-11 (48. tur — 186 + 187 + 188 + 189 + 190 + 191 KAPANIŞ)
**Branch:** `main` local (6 feat + 6 docs(ship) lineer, PUSH edilecek)
**Working tree:** temiz (git reset --hard + clean -fd, dış müdahale silindi)
**Durum:** 48. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1912/1912 test yeşil** (+12 skip), cov %91.85, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-11 — 48. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir" +
"B" seçimi (working tree'de 50+ dosya dış müdahale drift'i vardı;
`git reset --hard HEAD && git clean -fd` ile temizlendi) → 47. tur
adayları (186-191) tümü zincirleme.

1. **Görev 186** — vault verify webhook payload timestamp (`a6d76ec`)
   - SPEC 165 payload'a `timestamp: ISO 8601` (SPEC 180 ai-cli kardeşi).
   - Toplam alan: 8 → 9.
   - +2 test (ISO regex + alan sayısı).

2. **Görev 187** — metrics webhook payload timestamp (`99a72c6`)
   - SPEC 064 payload'a `timestamp` (SPEC 180/186 kardeşi).
   - SPEC 169 `alert_window_minutes` yolu AYNI.
   - +3 test.

3. **Görev 188** — vault verify --schema alert_options + alert_payload (`b220892`)
   - SPEC 175/181 kalıbı vault verify için.
   - `alert_options` 1 (SPEC 165), `alert_payload` 9 (SPEC 165 8 + SPEC 186 1).
   - Prometheus'a EKLENMEDİ (YAGNI; 4 metric aile korunur).
   - +5 test.

4. **Görev 189** — archive --schema alert_options + alert_payload (`fd42ac1`)
   - SPEC 175/181/188 kalıbı archive parent şeması için.
   - SPEC 176 --restore --alert-webhook payload 6 alan (SPEC 182 restore
     şeması ile paritel; parent burada da tekrarlar).
   - Prometheus'a EKLENMEDİ (YAGNI).
   - +5 test.

5. **Görev 190** — vault backup --schema alert_options + alert_payload (`d2a7612`)
   - SPEC 175/181/188/189 kalıbı vault backup için.
   - SPEC 178 6 phase (backup/prune/split/encrypt) `phase` alanı desc'inde belgelendi.
   - +5 test.

6. **Görev 191** — atlas-ci-status.yml webhook payload timestamp (`c49bdd1`)
   - SPEC 141 payload heredoc'una `"timestamp":"$ts"` (SPEC 185 workflow-CLI parity).
   - `ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)` ISO 8601 UTC.
   - Mevcut 5 alan DOKUNULMADI.
   - +3 workflow test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge.
   **12 lineer commit** (6 feat + 6 docs(ship)); 2026-07-31 kalıbı
   yine 6/6 tekrar etti (Windows filesystem sync — her ship.md ayrı
   commit gerekli).

---

## Sıradaki Karar (kullanıcıya sunulacak)

48. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 192 — `atlas doctor --alert-webhook` payload timestamp:**
  SPEC 180/186/187/191 kardeşi doctor için (SPEC 168 payload +
  SPEC 177 strict + SPEC 192 timestamp).
- **Görev 193 — `atlas-vault.yml` webhook step:** vault backup yaşam
  döngüsünde CI'da webhook YOK (mevcut CLI SPEC 178 var, workflow
  eksik). SPEC 135/141/185/191 kalıbı.
- **Görev 194 — `atlas ai-cli status --schema` alert_options +
  alert_payload:** SPEC 181/188/189/190 kalıbı ai-cli için
  (SPEC 170 payload + SPEC 180 size_bytes/timestamp belgele).
- **Görev 195 — `atlas metrics --schema` alert_payload timestamp
  ekleme:** SPEC 175 payload'a SPEC 187 timestamp alanı belge
  (SPEC 032.4 alan-ekleme; mevcut liste güncellenmeli).
- **Görev 196 — `atlas-metrics.yml` webhook payload timestamp:**
  SPEC 191 workflow kardeşi (SPEC 064/131 mevcut, timestamp eksik).
- **Görev 197 — `atlas doctor --schema` alert_payload timestamp
  ekleme:** SPEC 181 payload listesine SPEC 192 timestamp
  (SPEC 195 doctor kardeşi).

---

## Hızlı Bağlam

**main'e giren commit'ler (2026-08-11 48. tur):**
```
c49bdd1 feat(191): atlas-ci-status.yml webhook payload timestamp
d2a7612 feat(190): vault backup --schema alert_options + alert_payload
fd42ac1 feat(189): archive --schema alert_options + alert_payload
b220892 feat(188): vault verify --schema alert_options + alert_payload
99a72c6 feat(187): metrics --alert-webhook payload timestamp
a6d76ec feat(186): vault verify --alert-webhook payload timestamp
+ 6 docs(NNN) ship.md commit
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1912 passed, 12 skipped; cov 91.85%
uv run mypy src                # temiz
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI alanları (bu turda):**
- vault verify webhook payload +1 (SPEC 186 timestamp)
- metrics webhook payload +1 (SPEC 187 timestamp)
- vault verify --schema +2 bölüm (SPEC 188 alert_options + alert_payload)
- archive --schema +2 bölüm (SPEC 189)
- vault backup --schema +2 bölüm (SPEC 190)

**Yeni workflow davranışı:**
- `atlas-ci-status.yml` webhook payload +1 (SPEC 191 timestamp)

**Kritik sözleşme değişmezlikleri:**
- SPEC 165/064 webhook payload mevcut alanlar AYNI (bit-uyumlu ekleme).
- SPEC 136/149/154 --schema JSON şemaları AYNI + 2 yeni bölüm (SPEC 032.4).
- SPEC 128/151/158 Prometheus çıktıları AYNI (4 metric aile).
- SPEC 141 atlas-ci-status webhook mevcut 5 alan AYNI + 1 yeni.

**⚠️ 2026-07-31 kalıbı 48. turda 6/6 tekrar (regresyon):**
- 47. tur 0 ekstra docs commit iken 48. turda **6** — WT temizleme
  sonrası Windows FS gecikmesi arttı (git reset+clean sonrası ilk
  yazımlar). Öğrenilen: WT büyük reset'ten sonra ilk 6 görevde
  `sleep 3` yerine `sleep 5` gerekebilir; ampirik.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Bilinen küçük konular:**
- 48. tur öncesi WT'de 50+ dosya M/D vardı (dış müdahale — setup GUI/
  DOCTOR/portable script). Kullanıcı B seçti → `git reset --hard HEAD
  && git clean -fd`. **Temiz WT'de 48. tur çalıştırıldı**.
- CONTEXT.md, archive/, vault/daily+tasks+templates silindi (git clean).

---

## Kapanış Notları

- **1912 test yeşil** (1889 → 1912; bu tur +23)
- 12 lineer commit (6 feat + 6 docs(ship))
- Yeni CLI alanı: 8 (2 payload timestamp + 6 schema alert bölüm)
- Yeni workflow davranışı: 1 (ci-status webhook timestamp)
- Sıradaki tur için 6 aday (192–197).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-11)

| Tur | Test toplam | Delta |
|---|---:|---:|
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
| 44 | 1766 | +45 |
| 45 | 1811 | +45 |
| 46 | 1853 | +42 |
| 47 | 1889 | +36 |
| **48** | **1912** | **+23** |

Toplam **~122 feat/test-tur** commit + 27 docs commit; **+962 test**
(950 → 1912). Cov `%91.18 → %91.85`. 9 GHA workflow etkin.

# DEVAM NOKTASI — ATLAS

> ## TETİKLEYİCİ (agent talimatı — bu bloku her açılışta oku)
> Kullanıcı **"devam et"**, **"kaldığı yerden devam et"** veya
> **"projeye devam"** derse, başka soru sormadan:
> 1. Bu dosyanın **tamamını** oku.
> 2. `## Bu turda yapılan` bölümünden son turun sonucunu özetle.
> 3. `## Sıradaki Karar (kullanıcıya sunulacak)` altındaki adayları
>    listeleyip kısa bir seçim sorusuyla yeni turu başlat.
> 4. Kullanıcı onay verene kadar YIKICI işlem yapma.
> 5. Zorunlu Döngü'ye (`CLAUDE.md` §Zorunlu Döngü) gir.

**Son çalışma:** 2026-08-11 (49. tur — 192 + 193 + 194 + 195 + 196 + 197 KAPANIŞ)
**Branch:** `main` local (6 feat + 6 docs(ship) lineer, PUSH edilecek)
**Working tree:** temiz.
**Durum:** 49. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1934/1934 test yeşil** (+12 skip), cov %91.86, mypy/ruff/scan temiz.

---

## Bu turda yapılan (2026-08-11 — 49. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir" → 48. tur
adayları (192-197) tümü zincirleme.

1. **192** — doctor webhook payload timestamp — `timestamp` SPEC 168
   payload'a 5. anahtar (SPEC 180/186/187/191 kardeşi). SPEC 177
   testi 4→5 alan güncellendi. +3 test.

2. **193** — atlas-vault.yml webhook step — backup step `id=backup +
   continue-on-error + rc=$?`; yeni `Post vault-backup alert webhook`
   step (SPEC 135/141/185/191 kalıbı; payload alert+rc+run_id+sha+
   timestamp). +4 workflow test.

3. **194** — ai-cli status --schema alert_options + alert_payload
   (SPEC 175/181 kalıbı ai-cli için) — 1 seçenek + 8 payload alan
   (SPEC 170 6 + SPEC 180 2). +5 test.

4. **195** — metrics --schema alert_payload timestamp ekle (SPEC 187
   belge) — 14. alan `timestamp` (spec=187, when=webhook only). +3 test.

5. **196** — atlas-metrics.yml webhook step SPEC 187 belge — step adı
   SPEC 187/196 referansı; CLI zaten timestamp ekler (heredoc yok).
   +3 workflow test.

6. **197** — doctor --schema alert_payload timestamp ekle (SPEC 192
   belge) — 5. alan; SPEC 181 testinde alan sayısı 4→5. +4 test.

7. **Kalite kapıları:** 12 lineer commit (6 feat + 6 docs(ship));
   2026-07-31 kalıbı 6/6 tekrar (WT büyük reset sonrası FS gecikmesi
   arttı — 48. tur aynı).

---

## Sıradaki Karar

49. tur adayları tamamlandı. Yeni 6 aday:

- **198** — `archive --schema` `alert_payload` timestamp yolu belge
  (SPEC 176 payload'da timestamp YOK — CLI'ya ekleme veya "yok" belgele)
- **199** — `vault backup --schema` `alert_payload` timestamp ekle
  (SPEC 178'e CLI-tarafı timestamp ekleme + schema belge)
- **200** — `vault verify --alert-webhook` SPEC 195 kalıbı `alert_options`
  content genişletme (webhook only vs always ayırıcı)
- **201** — `atlas-doctor.yml` webhook payload'ta run_id/sha `timestamp`
  ile beraber `event` alanı (SPEC 141 kardeşi)
- **202** — `ai-cli status --alert-webhook` payload `strict` alanı
  (SPEC 177 kalıbı; --strict flag geldiğinde payload'a yansır)
- **203** — `atlas archive --restore --alert-webhook` payload `timestamp`
  (SPEC 176 → SPEC 180/186/187/191/192 kardeşi)

---

## Hızlı Bağlam

**Yeni CLI/workflow davranışı (bu turda):**
- doctor webhook +timestamp (192)
- vault backup workflow yeni webhook step (193)
- ai-cli status schema alert_options+payload (194)
- metrics schema alert_payload timestamp belgele (195)
- atlas-metrics workflow SPEC 187 belge (196)
- doctor schema alert_payload timestamp belgele (197)

**Kritik değişmezlikler:**
- SPEC 168/170/178 mevcut CLI payload alanları AYNI (bit-uyumlu ekleme).
- SPEC 041 vault backup davranışı AYNI (id=backup + continue-on-error
  eklendi ama backup çıktısı ve davranışı korundu).
- SPEC 064 metrics CLI davranışı AYNI (SPEC 187 timestamp CLI'da).
- SPEC 148/029/032 exit code semantikleri AYNI.

**⚠️ 2026-07-31 kalıbı 49. turda 6/6 tekrar (47 = 0, 48 = 6, 49 = 6):**
- Windows FS sync gecikmesi kalıcı hâle geldi.
- Ampirik: `sleep 4-5` ilk 2 test denemesinde bile ship.md yakalamıyor.
- 50. tur için hipotez: `os.fsync`/`git status --refresh` ile force
  refresh; ya da `Write` sonrası `git add -A pipeline/tasks/NNN/`
  yerine dosya listesini elle enumere et.

**Docker YASAK:** yürürlükte.

---

## Kapanış

- **1934 test yeşil** (1912 → 1934; bu tur +22)
- 12 lineer commit (6 feat + 6 docs(ship))
- Yeni schema alan: 4 (metrics/doctor timestamp + ai-cli 8 payload +
  ai-cli 1 option)
- Yeni CLI payload alan: 1 (doctor timestamp)
- Yeni workflow davranışı: 2 (atlas-vault yeni webhook step +
  atlas-metrics step adı SPEC 187 belge)
- Sıradaki tur için 6 aday (198–203).

## Toplu istatistik (son 15 tur)

| Tur | Test | Δ |
|---|---:|---:|
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
| 48 | 1912 | +23 |
| **49** | **1934** | **+22** |

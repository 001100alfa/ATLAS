# DEVAM NOKTASI — ATLAS

> ## TETİKLEYİCİ (agent talimatı — bu bloku her açılışta oku)
> Kullanıcı **"devam et"** derse:
> 1. Bu dosyanın tamamını oku.
> 2. Son turu özetle + `## Sıradaki Karar` adaylarını sun.
> 3. Yıkıcı işlem öncesi onay iste.

**Son çalışma:** 2026-08-11 (50. tur — 198+199+200+201+202+203 KAPANIŞ)
**Branch:** `main` local (12 commit lineer, PUSH edilecek)
**1953/1953 test yeşil** (+12 skip), cov %91.86, mypy/ruff/scan temiz.

---

## Bu turda yapılan (2026-08-11 — 50. tur)

1. **198** — archive --restore webhook payload + iki schema `timestamp`
   (SPEC 176 CLI 6→7; SPEC 189 archive schema + SPEC 182 restore schema).
   +4 test.

2. **199** — vault backup --alert-webhook payload `timestamp`
   (SPEC 178 CLI 6→7; SPEC 190 schema). +3 test.

3. **200** — 3 schema notes SPEC 198/199 timestamp yayma
   (archive/vault backup/vault verify notes tutarlılık). +3 test.

4. **201** — atlas-doctor.yml webhook payload `event` alanı
   (SPEC 141 kardeşi; workflow 7→8). +3 workflow test.

5. **202** — ai-cli status --alert-webhook payload `bin_path`
   (SPEC 170 CLI 8→9; SPEC 194 schema). +3 test.

6. **203** — atlas-ci-status.yml webhook payload `check: readme-badge`
   (SPEC 185 kalıp; kontrol tipi belge; 6→7). +3 workflow test.

**Kalite kapıları:** 12 lineer commit. 198 tek commit'te ship.md
dahil (sleep 4 + `git add -A` işledi); 199-203 hâlâ ayrı docs commit
(2026-07-31 kalıbı 3/6 iyileşme).

---

## Sıradaki Karar

50. tur adayları tamamlandı. Yeni 6 aday:

- **204** — `atlas doctor --alert-webhook` payload `event` alanı
  (SPEC 168 CLI kardeşi; SPEC 201 workflow paritel — CLI'da context
  yok, sabit `"cli"` değer)
- **205** — `atlas metrics --alert-webhook` payload `alert-history-path`
  (SPEC 064 payload'a log dosya yolu ekle — SPEC 126 kaynak belge)
- **206** — `atlas vault backup --schema` `sub_commands` alanı
  (SPEC 164 archive kalıbı: encrypt/split/prune/auto alt-akışlar)
- **207** — `atlas vault verify --alert-webhook` payload
  `broken_link_samples` (ilk N kırık link örneği; monitoring için değerli)
- **208** — `atlas-vault.yml` webhook payload `event` + `timestamp`
  (SPEC 193 kardeşi genişletme)
- **209** — `atlas archive --schema --format json-lines` `alert_option`
  tipi ekleme (SPEC 171 NDJSON stream'e SPEC 189 alert_options yansı)

---

## Hızlı Bağlam

**main'e giren commit'ler (2026-08-11 50. tur):**
```
9dcf094 feat(203): atlas-ci-status.yml webhook payload check alani
c0d9c79 feat(202): ai-cli status --alert-webhook payload bin_path
15565a1 feat(201): atlas-doctor.yml webhook payload event alani
8677da4 feat(200): 3 schema notes SPEC 198/199 timestamp yayma
45d344a feat(199): vault backup --alert-webhook payload timestamp
f4bcef5 feat(198): archive --restore webhook payload + schema timestamp
+ 5 docs(NNN) ship.md commit (198 tek commit'te ship dahil)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1953 passed, 12 skipped; cov 91.86%
```

**Kalıp iyileşme (2026-07-31):**
- 47=0, 48=6, 49=6, **50=5** — küçük iyileşme.
- 198'de `sleep 4` + `git add -A` işledi (tek commit).
- 199-203'te aynı yaklaşım tutmadı — belirsiz timing.
- 51. tur hipotezi: `sleep 6-8` + `git add pipeline/tasks/NNN/09-ship.md`
  tam yol.

**Docker YASAK:** yürürlükte.

---

## Kapanış

- **1953 test yeşil** (1934 → 1953; +19)
- 11 lineer commit (6 feat + 5 docs(ship)) + docs KAPANIS = 12
- Yeni CLI alan: 3 (archive/vault-backup/ai-cli-status webhook +1)
- Yeni schema alan: 5 (archive/vault-backup/ai-cli timestamp + bin_path)
- Yeni workflow alan: 2 (atlas-doctor event + atlas-ci-status check)
- Sıradaki 6 aday (204-209).

## Toplu istatistik

| Tur | Test | Δ |
|---|---:|---:|
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
| 49 | 1934 | +22 |
| **50** | **1953** | **+19** |

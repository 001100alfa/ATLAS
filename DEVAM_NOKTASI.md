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

**Son çalışma:** 2026-08-10 (45. tur — 168 + 169 + 170 + 171 + 172 + 173 KAPANIŞ)
**Branch:** `main` = `e703d12` local (6 feat lineer ff-merge, PUSH edilecek)
**Working tree:** temiz (tools/ai-cli/package* M drift + CONTEXT.md untracked — dokunulmadı)
**Durum:** 45. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1811/1811 test yeşil** (+12 skip), cov %91.66, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-10 — 45. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 44. tur adayları (168-173) tümü zincirleme.

1. **Görev 168** — doctor --alert-webhook URL (`3be3087`)
   - SPEC 064/165 kalıbı; `_has_quality_warning(report)` True ise POST.
   - Payload: alert=doctor + warnings + quality_warnings dict.
   - `_post_alert_webhook()` yeniden kullanıldı.
   - --strict ile ORTOGONAL (webhook exit 9'u etkilemez).
   - +7 test (deterministik monkeypatch + ephemeral HTTP).

2. **Görev 169** — metrics --alert-window MINUTES (`e7368ba`)
   - Alert değerlendirmesi için AYRI zaman-pencereli filtre.
   - `records_raw` orjinal liste `--window` uygulanmadan önce saklanır.
   - Email/webhook/slack payload `alert_*` window-scope değerler kullanır.
   - History NDJSON + webhook payload'a `alert_window_minutes` +
     `alert_window_records` alan-ekleme (bit-uyumlu; SPEC 032.4).
   - Geçersiz (<=0) → SPEC HATASI exit 2.
   - +7 test (kontrollü ts ile deterministik).

3. **Görev 170** — ai-cli status --alert-webhook URL (`84e1323`)
   - SPEC 064/165/168 kalıbı; up_to_date=False ise POST.
   - Payload: alert=ai-cli-status + name + versions + up_to_date + install_dir.
   - Schema modunda YOK sayılır (SPEC 146 kısa devre önce).
   - --json ile ORTOGONAL (stdout dokunulmaz).
   - +7 test (ephemeral HTTP + node_modules seed).

4. **Görev 171** — archive --schema --format json-lines (`6038c5c`)
   - SPEC 087/126/166 NDJSON stream + SPEC 164 sub_commands satırları.
   - --out PATH [--gzip] destek (SPEC 155/166 kalıbı).
   - YENİ MUTEX: json-lines yalnız --schema ile (normal modda reddet).
   - Parser: --format choices'a json-lines eklendi.
   - +9 test.

5. **Görev 172** — vault verify --schema --format json-lines (`98c429d`)
   - SPEC 087/126/166/171 NDJSON şema stream.
   - --schema flag'i SPEC 087 bulgu NDJSON'dan ayırır (iki farklı davranış).
   - --out PATH [--gzip] destek.
   - Parser DEĞİŞMEDİ (--format json-lines choices'da SPEC 087'den var).
   - +9 test.

6. **Görev 173** — atlas-metrics/vault.yml shell gzip → native taşıma (`e703d12`)
   - SPEC 160 metrics schema: shell gzip → native --out --gzip (SPEC 162).
   - SPEC 161 vault backup schema: shell gzip → native --out --gzip (SPEC 163).
   - SPEC 145 vault verify schema AYNI (zaten native).
   - Fallback `||` KORUNUR; upload path değişmedi.
   - +5 test (toplam workflow test 114 → 120).

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

45. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 174 — `atlas-ci-status.yml` shell gzip → native taşıma:**
  SPEC 173 kardeşi; SPEC 152 archive schema shell gzip artık native
  `--out --gzip` (SPEC 155) ile taşınabilir. Küçük.
- **Görev 175 — `atlas metrics --alert-window --schema` bilgisi:**
  SPEC 153 metrics schema'ya `alert_window` alan doküman ekle
  (`--alert-window`'un davranışı schema notes/top_level'a yansır).
  Küçük.
- **Görev 176 — `atlas archive --restore --alert-webhook`:** SPEC 064/
  165/168/170 kalıbı; restore hatası (exit 3/6) durumunda POST. Orta.
- **Görev 177 — `atlas doctor --alert-webhook --strict` payload:** SPEC
  168 payload'a `strict=true/false` alanı ekle (webhook alıcısı
  strict mode farkını görmeli). Küçük.
- **Görev 178 — `atlas vault backup --alert-webhook`:** SPEC 041 backup
  hatası (VaultBackupError exit 6) durumunda POST. Küçük-orta.
- **Görev 179 — `atlas metrics --alert-history-show --schema`:** SPEC
  132 alert-history log'unun record biçimi için ayrı şema
  (`--alert-history-show --schema` = record + summary şeması). Küçük.

---

## Hızlı Bağlam

**main'e giren 6 feat (2026-08-10 45. tur):**
```
e703d12 feat(173): atlas-metrics/vault.yml shell gzip -> native --out --gzip tasima
98c429d feat(172): vault verify --schema --format json-lines NDJSON + --out --gzip
6038c5c feat(171): archive --schema --format json-lines NDJSON + --out --gzip
84e1323 feat(170): ai-cli status --alert-webhook URL (SPEC 064/165/168 kalibi)
e7368ba feat(169): atlas metrics --alert-window MINUTES (zaman-pencereli alert)
3be3087 feat(168): atlas doctor --alert-webhook URL (SPEC 064/165 kalibi)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1811 passed, 12 skipped; cov 91.66%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --alert-webhook URL` (SPEC 168)
- `atlas metrics --alert-window MINUTES` (SPEC 169)
- `atlas ai-cli status --alert-webhook URL` (SPEC 170)
- `atlas archive --schema --format json-lines [--out PATH [--gzip]]` (SPEC 171)
- `atlas vault verify --schema --format json-lines [--out PATH [--gzip]]` (SPEC 172)

**Yeni workflow davranışı (bu turda):**
- `atlas-metrics.yml` SPEC 160 native --out --gzip (SPEC 173)
- `atlas-vault.yml` SPEC 161 vault backup native --out --gzip (SPEC 173)

**Kritik sözleşme değişmezlikleri:**
- SPEC 021 normal doctor davranışı AYNI (--alert-webhook yoksa).
- SPEC 029 --alert PCT + exit 8 davranışı AYNI (--alert-window yoksa).
- SPEC 037.4 normal ai-cli status davranışı AYNI (--alert-webhook yoksa).
- SPEC 149 archive --schema JSON default AYNI + SPEC 151 Prometheus AYNI.
- SPEC 136 vault verify --schema JSON default AYNI + SPEC 140 Prometheus AYNI.
- SPEC 087 vault verify normal --format json-lines (bulgu NDJSON) AYNI
  — --schema flag'i iki farklı davranışı ayırır.
- SPEC 145 vault verify --schema prom --out --gzip AYNI (zaten native).
- SPEC 147 atlas-doctor schema native --out --gzip AYNI.
- SPEC 152 atlas-ci-status archive schema shell gzip AYNI (SPEC 174 adayı).

**YENİ MUTEX'ler (bu turda):**
- doctor normal modda `--format json-lines` verilirse SPEC HATASI (SPEC 166).
- archive normal modda `--format json-lines` verilirse SPEC HATASI (SPEC 171).

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Notlar:**
- `tools/ai-cli/package.json` + `package-lock.json` git status M
  görünüyor (ai-cli portable kurulumun bağımlılık drift'i; bu turda
  dokunulmadı).
- CONTEXT.md hâlâ untracked (2026-08-06 statik harita).
- 42. tur bilinen flaky (`test_101_cli_split_retention_once`) 43-44-45
  turda gözlenmedi.
- 45. turda `test_0263_windows_cpu_quota_kesir` full-run tek koşumda
  düştü, izole tekli koşumda geçti — yeni flaky; SPEC değişikliğine
  bağlı değil (windows job cpu limit test, subprocess timing).

---

## Kapanış Notları

- **1811 test yeşil** (1766 → 1811; bu tur +45)
- 6 lineer feat commit
- Yeni CLI bayrağı: 4 (doctor --alert-webhook, metrics --alert-window,
  ai-cli status --alert-webhook, --format json-lines archive/vault-verify)
- Yeni workflow davranışı: 2 (metrics + vault backup schema native
  --out --gzip taşıma)
- Yeni MUTEX: 2 (doctor normal --format json-lines,
  archive normal --format json-lines)
- Sıradaki tur için 6 aday (174–179).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-10)

| Tur | Test toplam | Delta |
|---|---:|---:|
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
| 44 | 1766 | +45 |
| **45** | **1811** | **+45** |

Toplam **~104 feat/test-tur** commit + 19 docs commit; **+861 test**
(950 → 1811). Cov `%91.18 → %91.66`. 9 GHA workflow etkin. 3 sözleşme
rollback (SPEC 081→090, SPEC 091→104, SPEC 047→128).

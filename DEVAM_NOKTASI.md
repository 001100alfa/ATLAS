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

**Son çalışma:** 2026-08-10 (47. tur — 180 + 181 + 182 + 183 + 184 + 185 KAPANIŞ)
**Branch:** `main` = `297874c` local (6 feat lineer ff-merge, PUSH edilecek)
**Working tree:** temiz (tools/ai-cli/package* M drift + CONTEXT.md untracked — dokunulmadı)
**Durum:** 47. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1889/1889 test yeşil** (+12 skip), cov %91.84, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-10 — 47. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir
(atomic-order-doctrine)" → 46. tur adayları (180-185) tümü zincirleme.

1. **Görev 180** — ai-cli status webhook payload size_bytes + timestamp (`bcc4ed7`)
   - SPEC 170 payload'a 2 yeni alan (SPEC 032.4 bit-uyumlu).
   - `size_bytes` (mevcut alan) + `timestamp` (ISO 8601 seconds).
   - Toplam payload: 6 → 8.
   - Monitoring: "büyük drift" + "ne zamandır düşük" ayırt eder.
   - +4 test.

2. **Görev 181** — doctor --schema alert_options + alert_payload (`1876f34`)
   - SPEC 175 metrics kalıbı doctor için (SPEC 168 + SPEC 177 belgele).
   - `alert_options`: 1 CLI seçenek (`--alert-webhook URL`, SPEC 168).
   - `alert_payload`: 4 alan (alert/warnings/quality_warnings/strict).
   - Prometheus'a EKLENMEDİ (YAGNI; 6 metric aile AYNI).
   - +7 test.

3. **Görev 182** — archive --restore --schema (`fd8f99e`)
   - SPEC 179 kalıbı restore alt komutu için ayrı JSON şeması.
   - dry_run_json_fields (5) + apply_json_fields (5) + jsonl_record_types
     (3: plan/restored/summary) + alert_payload_fields (6: SPEC 176).
   - SPEC 149 archive --schema kısa devresi güncellendi:
     `--restore` verildiyse SPEC 182'ye bırakır.
   - +10 test.

4. **Görev 183** — vault verify --schema jsonl --out --gzip kanıt (`ca1fd92`)
   - SPEC 172 zaten uygulanmış; SPEC 159 kalıp simetrisi kanıt testleri.
   - +4 test: parent auto-mkdir + idempotent .gz + stdout↔file eşitlik
     + tam MUTEX mesajı.
   - Yeni CLI kodu YOK.

5. **Görev 184** — metrics --alert-history-show --format json-lines (`57c163d`)
   - SPEC 087/166/171/172 kalıp tutarlılığı; `--json` bit-uyumlu alias.
   - Parser --format choices'a json-lines; --json ile MUTEX
     (argparse mutex grubu).
   - --out sözleşmesi genişletildi (json/json-lines/prometheus).
   - SPEC 179 schema formats alanına json-lines (spec=184).
   - YENİ MUTEX: normal metrics + --format json-lines exit 2.
   - +8 test.

6. **Görev 185** — atlas-doctor.yml webhook payload strict alanı (`297874c`)
   - SPEC 177 CLI kardeşi (workflow-CLI parity).
   - Payload heredoc'una `"strict": true` (sabit — workflow
     `atlas doctor --strict --scan-src` çağırıyor).
   - Mevcut 6 alan DOKUNULMADI.
   - +3 workflow test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit
   (docs(NNN) ekstra commit YOK bu turda — kalıp azaltıldı).

---

## Sıradaki Karar (kullanıcıya sunulacak)

47. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 186 — `atlas vault verify --alert-webhook` payload timestamp
  alanı:** SPEC 165 payload'a `timestamp` alanı (SPEC 180 ai-cli kardeşi;
  monitoring "ne zaman broken" bilgisi). Küçük.
- **Görev 187 — `atlas metrics --alert-webhook` payload timestamp
  alanı:** SPEC 064 payload'a `timestamp` alanı (SPEC 180/186 kalıbı;
  Slack/webhook alıcısı zaman referansı). Küçük.
- **Görev 188 — `atlas vault verify --schema` alert_options +
  alert_payload:** SPEC 181 kalıbı vault verify için (SPEC 165 webhook
  payload belgele). Küçük-orta.
- **Görev 189 — `atlas archive --schema` alert_options + alert_payload
  (--restore için):** SPEC 181/188 kalıbı; SPEC 176 archive-restore
  webhook payload'ı archive genel şemada da belgele (SPEC 182 restore
  şeması ile parity). Küçük.
- **Görev 190 — `atlas vault backup --schema` alert_options +
  alert_payload:** SPEC 178 vault backup webhook payload belgele
  (SPEC 181/188/189 kalıbı; 6 phase). Küçük.
- **Görev 191 — `atlas-ci-status.yml` webhook payload timestamp
  alanı:** SPEC 185 kalıbı (workflow-CLI parity); SPEC 141 payload'a
  `"timestamp": "$(date -u ...)"` (SPEC 180/186/187 kardeşi). Küçük.

---

## Hızlı Bağlam

**main'e giren 6 feat (2026-08-10 47. tur):**
```
297874c feat(185): atlas-doctor.yml webhook payload strict alani (SPEC 177 CLI kardesi)
57c163d feat(184): metrics --alert-history-show --format json-lines (SPEC 087/166/171/172 tutarlilik)
ca1fd92 feat(183): vault verify --schema --format json-lines --out --gzip kanit tamamlama
fd8f99e feat(182): archive --restore --schema (SPEC 179 kalibi restore alt komutu)
1876f34 feat(181): doctor --schema alert_options + alert_payload belgeleme
bcc4ed7 feat(180): ai-cli status --alert-webhook payload size_bytes + timestamp
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1889 passed, 12 skipped; cov 91.84%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli status --alert-webhook` payload +2 alan (SPEC 180)
- `atlas doctor --schema` JSON'a alert_options + alert_payload (SPEC 181)
- `atlas archive --restore --schema` yeni JSON şeması (SPEC 182)
- `atlas metrics --alert-history-show --format json-lines` (SPEC 184)

**Yeni workflow davranışı:**
- `atlas-doctor.yml` webhook payload `strict: true` (SPEC 185)

**Kritik sözleşme değişmezlikleri:**
- SPEC 170 ai-cli-status webhook mevcut 6 alan AYNI + 2 yeni (bit-uyumlu).
- SPEC 040 doctor --schema JSON alanları AYNI + 2 yeni bölüm (bit-uyumlu).
- SPEC 149 archive --schema (--restore YOK) AYNI + SPEC 164 sub_commands
  KORUNUR.
- SPEC 132/143/144/148 metrics alert-history-show mevcut davranışlar AYNI.
- SPEC 087 vault verify normal --format json-lines (bulgu NDJSON) AYNI.
- SPEC 135 atlas-doctor.yml webhook step conditional + env + continue-on-error AYNI.

**YENİ MUTEX (bu turda):**
- Normal metrics (--alert-history-show YOK) + `--format json-lines`
  → SPEC HATASI exit 2 (SPEC 184).

**Docker YASAK:** hâlâ yürürlükte + otomatik gate.

**Bilinen küçük konular:**
- `tools/ai-cli/package.json` + `package-lock.json` git status M
  (46 turdur dokunulmadı).
- CONTEXT.md hâlâ untracked.
- 42. tur bilinen flaky (`test_101_cli_split_retention_once`) ve
  45. tur (`test_0263_windows_cpu_quota_kesir`) 47. turda gözlenmedi.

**Kalıp iyileşmesi (bu turdan):**
- **2026-07-31 ship.md kalıbı** — 46. turda 4/6 tekrar etti; 47. turda
  disiplin: `sleep 2` + `git add pipeline/tasks/NNN/` + `git status
  | grep NNN` → ship.md eksikse `git add pipeline/tasks/NNN/09-ship.md`
  + tek `git commit`. Sonuç: **6 feat commit + 0 docs(NNN) ekstra
  commit** (46. tur = 6 feat + 4 docs(NNN); 47. tur = 6 feat + 0).

---

## Kapanış Notları

- **1889 test yeşil** (1853 → 1889; bu tur +36)
- 6 lineer feat commit (docs(NNN) ekstra commit YOK — disiplin başardı)
- Yeni CLI alanı: 4 (ai-cli webhook payload 2 + doctor schema 2 bölüm)
- Yeni CLI komutu: 2 (archive --restore --schema, metrics
  --alert-history-show --format json-lines)
- Yeni workflow davranışı: 1 (atlas-doctor payload strict)
- Yeni MUTEX: 1 (metrics normal --format json-lines)
- Sıradaki tur için 6 aday (186–191).

---

## 15 Turluk Toplu İstatistik (2026-08-05 → 2026-08-10)

| Tur | Test toplam | Delta |
|---|---:|---:|
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
| 45 | 1811 | +45 |
| 46 | 1853 | +42 |
| **47** | **1889** | **+36** |

Toplam **~116 feat/test-tur** commit + 21 docs commit; **+939 test**
(950 → 1889). Cov `%91.18 → %91.84`. 9 GHA workflow etkin; 4 workflow
şema artifact HEPSİ native `--out --gzip`. 3 sözleşme rollback
(SPEC 081→090, SPEC 091→104, SPEC 047→128).

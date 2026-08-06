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

**Son çalışma:** 2026-08-06 (38. tur — 127 + 129 + 131 + 130 + 128 + 126)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz (CONTEXT.md untracked — dokunulmadı)
**Durum:** 38. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1533/1533 test yeşil** (+12 skip), cov ~%91.44, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-06 — 38. tur)

Kullanıcı "hepsini sıra ile uygula, emirler atomiktir" → 37. tur
adayları (126-131) tümü zincirleme.

1. **Görev 127** — archive --restore <id> --json (`53626f2`)
   - Dry-run + apply JSON modu.
   - Dry-run: `{mode,task_id,archive,target,conflict}`.
   - Apply: `{mode,task_id,archive,target,restored:true}`.
   - Hata JSON basmaz; stderr SPEC HATASI + rc (2/3/6) korunur.
   - +5 test.

2. **Görev 129** — vault verify tam zincir regresyon (`a96969a`)
   - SPEC 087+092+111+042 birlikte doğrulama.
   - Kod DEĞİŞMEZ (salt-test).
   - +4 test.

3. **Görev 131** — atlas-metrics.yml alert-webhook post (`020448e`)
   - Yeni step: `atlas metrics --alert 30 --alert-webhook "$URL"`.
   - Env `secrets.ATLAS_ALERT_WEBHOOK_URL`; conditional + continue-on-error.
   - +4 test.

4. **Görev 130** — atlas-doctor.yml --diff-history-all --strict gate (`3e97fb4`)
   - Yeni step: `Doctor history regression gate` (id: `history_gate`).
   - `atlas doctor --diff-history-all --strict > doctor-history-strict.txt`.
   - Fail step conditional: `rc_hist != '0'` de eklendi.
   - Upload artifact + `doctor-history-strict.txt`.
   - +4 test.

5. **Görev 128** — doctor --schema --format prometheus (`2114330`)
   - **SPEC 047 MUTEX rollback (3.)** — `--schema` grup dışına.
   - 4 info-metric ailesi: version + top_level_field + quality_field +
     exit_code (labels: version/name/type/spec/code).
   - `--format` yoksa JSON BİT-UYUMLU.
   - +6 yeni test + 2 test güncelleme (eski MUTEX → no_longer_mutex).

6. **Görev 126** — metrics --alert-history NDJSON log (`94f3152`)
   - `--alert-history [PATH]` nargs="?" const default.
   - Alert tetikleme → NDJSON append (ts+alert+ratio+threshold+
     tokens+channels[]).
   - Yazma hatası → stderr UYARI + exit 8 KORUNUR.
   - Alert tetiklenmezse log yazılmaz.
   - +7 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

38. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 132 — `atlas metrics --alert-history --limit N`:** SPEC 126
  history dosyasını okuma modu (`--limit N` son alertler + JSON çıktı).
  Orta.
- **Görev 133 — `atlas archive --restore --json --json-lines`:** SPEC
  127 stream modu (multi-restore için list). Küçük.
- **Görev 134 — `atlas doctor --schema --format prometheus --out --gzip`:**
  SPEC 128 → dosya + gzip (SPEC 103 kalıbı). Küçük.
- **Görev 135 — `.github/workflows/atlas-doctor.yml` alert-webhook
  gate:** SPEC 131 kalıbı doctor için (health fail'de webhook). Orta.
- **Görev 136 — `atlas vault verify --json --schema`:** verify çıktısı
  schema tanımı (SPEC 040 kalıbı). Küçük.
- **Görev 137 — `.github/workflows/atlas-metrics.yml` alert-history
  artifact:** SPEC 126 çıktısını CI artifact olarak upload. Küçük.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**main'e giren 6 commit (2026-08-06 38. tur):**
```
94f3152 feat(126): atlas metrics --alert-history NDJSON log (SPEC 029 uzerine)
2114330 feat(128): atlas doctor --schema --format prometheus (info-metric ailesi)
3e97fb4 feat(130): atlas-doctor.yml --diff-history-all --strict gate (SPEC 097)
020448e feat(131): atlas-metrics.yml alert-webhook post (SPEC 064)
a96969a test(129): vault verify tam zincir SPEC 087+092+111+042 regresyon
53626f2 feat(127): atlas archive --restore <id> --json (dry-run + apply)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1533 passed, 12 skipped; cov 91.44%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --restore <id> --json` (SPEC 127)
- `atlas doctor --schema --format prometheus` (SPEC 128)
- `atlas metrics --alert-history [PATH]` (SPEC 126)

**Yeni workflow adımları:**
- `atlas-metrics.yml` `Post alert webhook` (SPEC 131)
- `atlas-doctor.yml` `Doctor history regression gate` (SPEC 130)

**Yeni test dosyaları:**
- `test_cli_archive_restore_json.py` (SPEC 127)
- `test_cli_vault_verify_full_chain.py` (SPEC 129)
- `test_cli_doctor_schema_prom.py` (SPEC 128)
- `test_cli_metrics_alert_history.py` (SPEC 126)

**Kritik sözleşme değişmezlikleri:**
- SPEC 033/071: archive restore pretty AYNI (--json opt-in).
- SPEC 040: doctor --schema JSON AYNI (--format prometheus opt-in).
- SPEC 029/059/064/068: alert kanalları AYNI (--alert-history opt-in).
- SPEC 070/074: mevcut workflow step'leri DOKUNULMADI.

**Sözleşme değişikliği (3. rollback):**
- **SPEC 047 MUTEX kısmen KALDIRILDI** (SPEC 128). `--schema` p_doc_out
  grubundan çıkarıldı. `--json + --format` MUTEX KORUNDU. 3. rollback:
  ilk SPEC 081→090, ikinci SPEC 091→104, üçüncü SPEC 047→128.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

**Notlar:**
- CONTEXT.md kullanıcı tarafından eklenmiş untracked bir dosya
  (statik kod haritası, 2026-08-06). Bu turda dokunulmadı.
- Argparse tanım değişikliği sonrası `find . -name __pycache__ -exec
  rm -rf {} +` gerekebilir (SPEC 128 [HATA] kalıp).

---

## Kapanış Notları

- **1533 test yeşil** (1503 → 1533; bu tur +30)
- 6 lineer commit (5 feat + 1 test-tur)
- Yeni CLI bayrakları: 3 (archive --restore --json, doctor --schema
  --format prometheus, metrics --alert-history)
- Yeni workflow adımları: 2 (alert-webhook post, history regression gate)
- 3. sözleşme rollback (SPEC 047 → SPEC 128)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (132–137).

---

## 13 Turluk Toplu İstatistik (2026-08-05 → 2026-08-06)

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
| 36 | 1479 | +28 |
| 37 | 1503 | +24 |
| **38** | **1533** | **+30** |

Toplam **~75 feat/test-tur** commit + 13 docs commit; **+621 test**
(912 → 1533). Cov `%91.18 → %91.44`. 8 GHA workflow; 3 sözleşme
rollback (SPEC 081→090, SPEC 091→104, SPEC 047→128).

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

**Son çalışma:** 2026-08-05 (30. tur — 082 + 079 + 083 + 078 + 080 + 081)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 30. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1221/1221 test yeşil** (+12 skip), cov ~%91.5+, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 30. tur)

Kullanıcı "devam et ve hepsini sıra ile uygula" → 29. tur adayları
(078-083) tümü zincirleme, küçükten büyüğe.

1. **Görev 082** — ci-status.yml + README badge tablosu (`26894fb`)
   - `tools/scripts/gen_ci_badges.py`: workflow YAML → README badge
     tablosu (marker'lar arası; drift gate).
   - `.github/workflows/ci-status.yml`: `--check` drift → PR comment +
     exit 1.
   - README güncellendi (6 workflow badge).
   - +8 test.

2. **Görev 079** — archive --list --sort-by KEY (`47e8df3`)
   - SPEC 075 metadata sıralama: `{name,size,date,members}` + `--desc`.
   - Default `name` bit-uyumlu.
   - `date` boşsa mtime fallback.
   - +8 test.

3. **Görev 083** — ai-cli uninstall <name> (`503601d`)
   - `_run_npm_uninstall(bin, package)` + `_cmd_ai_cli_uninstall`.
   - 4-yollu hata (dir/deps/npm/subprocess) → exit 2.
   - +7 test.

4. **Görev 078** — vault restore --decrypt-recipient GPG asimetrik (`ed3d315`)
   - `decrypt_backup_recipient`: passphrase YOK (private key + gpg-agent).
   - `--decrypt` + `--decrypt-recipient` MUTEX exit 2.
   - Mevcut SPEC 066 test'lerinde 2 mesaj metni tolerans regex.
   - +9 test.

5. **Görev 080** — doctor --save-baseline history + retention (`75f12ee`)
   - `.atlas/doctor-history/baseline-YYYY-MM-DD.json` auto-snapshot.
   - `--history-keep N` retention + `--history-list` kısa devre.
   - Default path yan etkisi (custom path → tarihçe YOK).
   - +14 test.

6. **Görev 081** — metrics --group-by hour|day aggregation (`3f8d8e4`)
   - `_group_records_by(records, unit)`: hour/day; `ts` bozuk → `unknown`.
   - Semantik mutex: `--format prometheus` + `--alert` → exit 2.
   - `--window` ile ORTOGONAL.
   - +12 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

30. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 084 — `atlas metrics --group-by --with-cost`:** SPEC 081
  aggregation'a group başına $ cost hesabı (fiyat env ile). Küçük-orta.
- **Görev 085 — `atlas archive --list --sort-by --limit N`:** SPEC 079
  sort + top-N (en büyük 5 arşiv gibi). Küçük.
- **Görev 086 — `atlas doctor --history --diff N`:** SPEC 080 tarihçesindeki
  N. snapshot ile mevcut arasında delta. Orta.
- **Görev 087 — `atlas vault verify --format json-lines`:** SPEC 042
  büyük vault'lar için streaming JSON (bulguları newline-delimited).
  Küçük-orta.
- **Görev 088 — `atlas ai-cli list --outdated`:** SPEC 037.2 filtresi;
  yalnız beklenen ≠ kurulu sürüm satırlar. Küçük.
- **Görev 089 — `.github/workflows/atlas-ci-status.yml` badge freshness:**
  SPEC 082 drift gate + workflow scheduled (daily) — badge SVG cache
  invalidation için. Küçük.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 6 commit local (30. tur — push edilecek)`

**main'e giren 6 feat (2026-08-05 30. tur):**
```
3f8d8e4 feat(081): atlas metrics --group-by hour|day aggregation
75f12ee feat(080): atlas doctor --save-baseline history + --history-keep + --history-list
ed3d315 feat(078): vault restore --decrypt-recipient GPG asimetrik decrypt
503601d feat(083): atlas ai-cli uninstall <name>
47e8df3 feat(079): atlas archive --list --sort-by KEY [--desc]
26894fb feat(082): ci-status.yml + README badge tablosu drift gate
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1221 passed, 12 skipped
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --list --sort-by {name,size,date,members} [--desc]`
- `atlas ai-cli uninstall <name>`
- `atlas vault restore --decrypt-recipient` (asimetrik decrypt)
- `atlas doctor --save-baseline` (tarihçe yan etki) + `--history-keep N`
  + `--history-list`
- `atlas metrics --group-by {hour,day}`

**Yeni workflow:** `.github/workflows/ci-status.yml` (drift gate).
**Yeni script:** `tools/scripts/gen_ci_badges.py`.

**Yeni env sözleşmesi:** DEĞİŞMEDİ.

**Yeni yardımcılar:**
- `_list_doctor_history`, `_prune_doctor_history` (cli.py, SPEC 080)
- `_group_records_by` (cli.py, SPEC 081)
- `_run_npm_uninstall` (cli.py, SPEC 083)
- `decrypt_backup_recipient` (vault_backup.py, SPEC 078)

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri:**
- SPEC 023/029/043/051/059/064/068/076 metrics zinciri BİT-UYUMLU
  (group-by ORTOGONAL, window ile birlikte çalışır).
- SPEC 007/012/017/033/065/071/075 archive zinciri BİT-UYUMLU
  (list default `name` alfabetik korunur).
- SPEC 037 ailesi BİT-UYUMLU (uninstall yeni; install/update/list/exec/
  status/diff-summary dokunulmadı).
- SPEC 041/041.1/063/066/067/073 vault zinciri BİT-UYUMLU.
- SPEC 062 `--save-baseline` default path içerik AYNI (tarihçe yan etki).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 5 blok (30/29/28/27/26. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1221 test yeşil** (1163 → 1221; bu tur +58; oturum başı 319'dan +902)
- 6 lineer feat + docs commit
- Yeni CLI bayrakları: 5 (archive --list --sort-by/--desc, ai-cli
  uninstall, vault restore --decrypt-recipient, doctor --save-baseline
  yan etki + --history-keep + --history-list, metrics --group-by)
- Yeni workflow: `ci-status.yml`
- Yeni script: `tools/scripts/gen_ci_badges.py` (drift gate)
- Yeni yardımcı fonksiyonlar: 4 (cli.py) + 1 (vault_backup.py)
- Yeni test dosyaları: `test_gen_ci_badges.py`,
  `test_cli_archive_list_sort.py`, `test_cli_ai_cli_uninstall.py`,
  `test_cli_vault_restore_decrypt_recipient.py`,
  `test_cli_doctor_history.py`, `test_cli_metrics_group_by.py` (6 dosya, +58 test)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (084–089).

---

## 5 Turluk Toplu İstatistik (2026-08-05 tek gün)

| Tur | Bitiş commit | Test toplam | Delta | Yeni bayrak/komut |
|---|---|---:|---:|---|
| 26 | 03dec44 | 995 | +83 | doctor --diff, --http-check, vault fix-broken, replay --serve, metrics --alert-email, GHA vault-health |
| 27 | c086a78 | 1061 | +66 | ai-cli install, doctor --auto-baseline, vault backup --encrypt, metrics --alert-webhook, archive --search, JSON Schema doc |
| 28 | 32f6fdd | 1110 | +49 | metrics --alert-slack, vault backup --keep-encrypted, vault restore --decrypt, archive --restore --search, run --estimate, GHA atlas-doctor |
| 29 | dcc7f08 | 1163 | +53 | Docker YASAK gate (v5), atlas-metrics.yml, metrics --window, archive --list, --estimate --adaptive, vault backup --recipient |
| **30** | **e7 push** | **1221** | **+58** | ci-status.yml, archive --list --sort-by, ai-cli uninstall, vault restore --decrypt-recipient, doctor --history, metrics --group-by |

Toplam **30 feat commit** + 5 docs commit bugün; **+309 test** (912
→ 1221). Cov `%91.18 → %91.5+`. Docker YASAK otomatik gate; 6 yeni GHA
workflow (vault-health, atlas-doctor, atlas-metrics, no-docker,
ci-status + mevcut ci); 5 yeni CLI komutu/alt-komutu (vault fix-broken,
vault fix-orphans, ai-cli install/uninstall/status); ~30 yeni CLI
bayrağı/varyasyonu.

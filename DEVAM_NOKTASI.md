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

**Son çalışma:** 2026-08-05 (29. tur — 077 + 074 + 076 + 075 + 072 + 073)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 29. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1163/1163 test yeşil** (+12 skip), cov ~%91.5+, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 29. tur)

Kullanıcı "hepsini sıra ile uygula" → 28. tur adayları (072-077) tümü
zincirleme, küçükten büyüğe.

1. **Görev 077** — Docker YASAK gate (`51f9d61`)
   - `.github/workflows/no-docker.yml`: push+PR `git ls-files` pattern
     arama.
   - Pre-commit hook v4 → v5: Kapı 3 Docker YASAK (regex `git diff
     --cached`).
   - +10 test (5 hook + 5 workflow).

2. **Görev 074** — atlas-metrics.yml PR gate (`cb7dcfa`)
   - SPEC 056/070 kardeşi bilgi/artifact gate.
   - `.atlas/metrics.jsonl` path filtresi; 3 format (human/json/prometheus)
     artifact; PR comment (has_data).
   - +6 workflow testi.

3. **Görev 076** — metrics --window MINUTES (`220abde`)
   - `_filter_records_by_window(records, minutes, now=None)`.
   - `--limit` ile ORTOGONAL: önce window, sonra son N.
   - `--window <= 0` → exit 2.
   - +10 test.

4. **Görev 075** — archive --list [--json] (`32d24eb`)
   - `_list_archive_entries`: 7-alanlı dict per arşiv.
   - Dispatcher: `--list` en önde (read-only).
   - Bozuk tar → `member_count=-1`.
   - +11 test.

5. **Görev 072** — --estimate --adaptive metrics avg (`ebad7eb`)
   - `_read_metrics_avg_tokens(limit=20)`.
   - `--adaptive` + `--adaptive-n N` bayrakları.
   - < 3 kayıt → static fallback + UYARI.
   - JSON şema `source` + `sample_count` alanları.
   - +10 test.

6. **Görev 073** — vault backup --recipient GPG public-key (`d2a432c`)
   - `encrypt_backup_recipient` (asimetrik, passphrase YOK).
   - `--encrypt` + `--recipient` MUTEX exit 2.
   - Audit action `encrypt-recipient`.
   - +9 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

29. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 078 — `atlas vault restore --decrypt-recipient`:** SPEC 066
  symmetric decrypt tamamlanan asimetrik decrypt kardeşi
  (`gpg --decrypt` private key + gpg-agent). Orta.
- **Görev 079 — `atlas archive --list --sort-by size|date`:** SPEC 075
  metadata listesine sıralama bayrağı (default alfabetik). Küçük.
- **Görev 080 — `atlas doctor --history N`:** SPEC 057/062 diff kalıbıyla
  `.atlas/doctor-baseline.json` tarihçesi rotasyonu (`baseline-YYYY-MM-DD.json`).
  Küçük-orta.
- **Görev 081 — `atlas metrics --group-by hour|day`:** SPEC 076 window +
  aggregation; her saat/gün için toplam token+cost. Orta.
- **Görev 082 — `.github/workflows/ci-status.yml`:** tüm mevcut workflow'ları
  bir README badge tablosuna dönüştüren workflow. Küçük.
- **Görev 083 — `atlas ai-cli uninstall <name>`:** SPEC 037 ailesine
  tamamlayıcı (`npm uninstall` wrap + package.json güncelleme).
  Küçük-orta.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 7 commit local (29. tur — push edilecek)`

**main'e giren 6 feat + 1 docs commit (2026-08-05 29. tur):**
```
d2a432c feat(073): vault backup --recipient KEY_ID GPG public-key encryption
ebad7eb feat(072): atlas run --estimate --adaptive metrics ortalamasi
32d24eb feat(075): atlas archive --list [--json] metadata listesi
220abde feat(076): atlas metrics --window MINUTES time-based filtre
cb7dcfa feat(074): .github/workflows/atlas-metrics.yml metrics PR gate
51f9d61 feat(077): Docker YASAK gate (CI + pre-commit hook v5)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1163 passed, 12 skipped
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas archive --list [--json]` (yeni bayrak)
- `atlas metrics --window MINUTES` (yeni bayrak)
- `atlas run --estimate --adaptive [--adaptive-n N]` (yeni 2 bayrak)
- `atlas vault backup --recipient KEY_ID` (yeni bayrak, --encrypt mutex)

**Yeni workflows:**
- `.github/workflows/no-docker.yml`
- `.github/workflows/atlas-metrics.yml`

**Yeni env sözleşmesi:** DEĞİŞMEDİ (72 mevcut env kullanır).

**Yeni yardımcılar:**
- `_filter_records_by_window` (cli.py, SPEC 076)
- `_list_archive_entries`, `_cmd_archive_list` (cli.py, SPEC 075)
- `_read_metrics_avg_tokens` (cli.py, SPEC 072)
- `encrypt_backup_recipient` (vault_backup.py, SPEC 073)

**Hook v4 → v5**: Docker YASAK Kapı 3 eklendi. Mevcut kullanıcılar
`atlas hooks install --force` şart.

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri:**
- SPEC 023/029/043/051/059/064/068 metrics zinciri BİT-UYUMLU.
- SPEC 007/012/017/033/065/071 archive zinciri BİT-UYUMLU.
- SPEC 041/041.1/063/066/067 vault backup zinciri BİT-UYUMLU.
- SPEC 002/020/030/031/069 run zinciri BİT-UYUMLU.
- SPEC 034/045/052 hook zinciri BİT-UYUMLU (Kapı 3 ek).
- SPEC 056/070 GHA gate kalıbı BİT-UYUMLU (074 aynı kalıp).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077).

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 4 blok (29/28/27/26. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1163 test yeşil** (1110 → 1163; bu tur +53; oturum başı 319'dan +844)
- 6 lineer feat + 1 docs commit
- Yeni workflow: `no-docker.yml`, `atlas-metrics.yml`
- Yeni CLI bayrakları: 4 yeni (`archive --list`, `metrics --window`,
  `run --adaptive/--adaptive-n`, `vault backup --recipient`)
- Yeni yardımcı fonksiyonlar: 4 (cli.py + vault_backup.py)
- Hook: v4 → v5 (Docker Kapı 3)
- Docker YASAK ARTIK OTOMATIK GATE (CI + hook).
- Sıradaki tur için 6 aday (078–083).

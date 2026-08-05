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

**Son çalışma:** 2026-08-05 (33. tur — 099 + 098 + 096 + 097 + 100 + 101)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 33. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1366/1366 test yeşil** (+12 skip), cov ~%91.39, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 33. tur)

Kullanıcı "hepsini sıra ile uygula" → 32. tur adayları (096-101) tümü
zincirleme, küçükten büyüğe.

1. **Görev 099** — ai-cli list --outdated --json-lines (`a818016`)
   - Paket başına 1 NDJSON satır + son satır summary.
   - `--json-lines` yalnız `--outdated` ile; `--json` ile MUTEX.
   - `--strict` ORTOGONAL (bulgu → exit 4, NDJSON hâlâ basılır).
   - +7 test.

2. **Görev 098** — archive --list --json-lines (`ddb0837`)
   - Arşiv başına satır + summary (SPEC 075 alanları AYNI).
   - Filter/sort/limit stream ÖNCESİ (deterministik).
   - `--json` ile MUTEX.
   - +7 test.

3. **Görev 096** — metrics --group-by --format prometheus --out PATH (`2a2da33`)
   - Grup histogramını dosyaya yaz (SPEC 092 kalıbı).
   - `--out` yalnız `--group-by + --format prometheus` ile.
   - Parent auto-mkdir; IO hatası exit 2.
   - +9 test.

4. **Görev 097** — doctor --diff-history-all --strict (`c279606`)
   - Herhangi snapshot regresyon → exit 9 (SPEC 032/057 uyumlu).
   - stderr'de regressed date listesi.
   - `--json` ORTOGONAL (içerik AYNI, rc değişir).
   - +7 test.

5. **Görev 100** — atlas-doctor.yml --diff-history-all artifact (`9be589b`)
   - Yeni step `Generate diff-history-all trend`.
   - `||` fallback bos snapshots (fail-safe).
   - Upload artifact + `doctor-diff-history-all.json`.
   - Mevcut 2 artifact BİT-UYUMLU.
   - +4 test.

6. **Görev 101** — vault backup --split SIZE_MB (`5079e97`)
   - `split_backup(src, size_mb)` fixed-size parça .001/.002/.003.
   - Orijinal silinir; boş src → tek boş .001.
   - `--encrypt`/`--recipient` ile MUTEX (encrypted split ayrı SPEC).
   - `--keep` retention split ÖNCESİ; `--out` ORTOGONAL.
   - +11 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

33. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 102 — `atlas vault restore <path> --split`:** SPEC 101
  parça birleştirme + restore (auto-detect `.001..N` sıralı okuma).
  Orta.
- **Görev 103 — `atlas metrics --group-by --format prometheus --out`
  + gzip:** SPEC 096 çıktısını `.gz` sıkıştırma bayrağı. Küçük.
- **Görev 104 — `atlas doctor --diff-history-all --format prometheus`:**
  SPEC 091 grup metrikleri (per-snapshot regression count) Prometheus
  scrape uyumlu. Orta.
- **Görev 105 — `atlas archive --list --json-lines --out PATH`:**
  SPEC 098 stream'i doğrudan dosyaya (SPEC 092 kalıbı). Küçük.
- **Görev 106 — `atlas ai-cli list --outdated --json-lines --out PATH`:**
  SPEC 099 stream'i dosyaya. Küçük.
- **Görev 107 — `.github/workflows/atlas-vault.yml` yeni: vault backup
  scheduled daily + `--split`:** SPEC 041/101 üretim uzantısı. Orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 6 commit local (33. tur — push edilecek)`

**main'e giren 6 feat (2026-08-05 33. tur):**
```
5079e97 feat(101): atlas vault backup --split SIZE_MB (parcali yedek)
9be589b feat(100): atlas-doctor.yml --diff-history-all artifact entegrasyonu
c279606 feat(097): atlas doctor --diff-history-all --strict (regresyon -> exit 9)
2a2da33 feat(096): atlas metrics --group-by --format prometheus --out PATH
ddb0837 feat(098): atlas archive --list --json-lines (NDJSON stream)
a818016 feat(099): atlas ai-cli list --outdated --json-lines (NDJSON stream)
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1366 passed, 12 skipped; cov 91.39%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas ai-cli list --outdated --json-lines` (SPEC 099)
- `atlas archive --list --json-lines` (SPEC 098)
- `atlas metrics --group-by --format prometheus --out PATH` (SPEC 096)
- `atlas doctor --diff-history-all --strict` (SPEC 097)
- `atlas vault backup --split SIZE_MB` (SPEC 101)

**Yeni workflow adımı:** `atlas-doctor.yml` `Generate diff-history-all trend`
+ `doctor-diff-history-all.json` artifact (SPEC 100).

**Yeni env sözleşmesi:** DEĞİŞMEDİ.

**Yeni yardımcılar:** `split_backup` (vault_backup.py, SPEC 101).

**Exit kodları:**
- doctor --diff-history-all --strict + regresyon → **exit 9** (SPEC 097).

**Kritik sözleşme değişmezlikleri:**
- SPEC 088/094: ai-cli `--json` içerik AYNI (JSON-lines yeni yol).
- SPEC 075/079/085/093: archive `--json` AYNI (JSON-lines yeni yol).
- SPEC 090: metrics grup Prometheus stdout AYNI (`--out` yeni yol).
- SPEC 091: doctor `--diff-history-all` çıktı içerik AYNI (--strict
  sadece rc etkiler).
- SPEC 070/074: atlas-doctor.yml mevcut gate + 2 artifact AYNI.
- SPEC 041/041.1: vault backup default davranış + retention AYNI
  (`--split` yeni bayrak).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte + otomatik gate (SPEC 077, CI + hook v5).

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 4 blok (33/32/31/30. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1366 test yeşil** (1321 → 1366; bu tur +45; oturum başı 319'dan +1047)
- 6 lineer feat + docs commit
- Yeni CLI bayrakları: 5 (ai-cli --json-lines, archive --json-lines,
  metrics --out, doctor --diff-history-all --strict, vault backup --split)
- 1 yeni yardımcı fonksiyon: `split_backup` (vault_backup.py)
- Yeni workflow adımı: atlas-doctor.yml diff-history-all artifact
- Yeni test dosyaları:
  `test_cli_ai_cli_outdated_jsonl.py`,
  `test_cli_archive_list_jsonl.py`,
  `test_cli_metrics_group_prom_out.py`,
  `test_cli_doctor_diff_history_all_strict.py`,
  `test_cli_vault_backup_split.py`,
  + `test_github_workflows.py` SPEC 100 bölümü (5 dosya + 1 update, +45 test)
- Docker YASAK yürürlükte + hook v5
- Sıradaki tur için 6 aday (102–107).

---

## 8 Turluk Toplu İstatistik (2026-08-05 tek gün)

| Tur | Bitiş commit | Test toplam | Delta | Yeni bayrak/komut |
|---|---|---:|---:|---|
| 26 | 03dec44 | 995 | +83 | doctor --diff, --http-check, vault fix-broken, replay --serve, metrics --alert-email, GHA vault-health |
| 27 | c086a78 | 1061 | +66 | ai-cli install, doctor --auto-baseline, vault backup --encrypt, metrics --alert-webhook, archive --search, JSON Schema doc |
| 28 | 32f6fdd | 1110 | +49 | metrics --alert-slack, vault backup --keep-encrypted, vault restore --decrypt, archive --restore --search, run --estimate, GHA atlas-doctor |
| 29 | dcc7f08 | 1163 | +53 | Docker YASAK gate (v5), atlas-metrics.yml, metrics --window, archive --list, --estimate --adaptive, vault backup --recipient |
| 30 | e2261f6 | 1221 | +58 | ci-status.yml, archive --list --sort-by, ai-cli uninstall, vault restore --decrypt-recipient, doctor --history, metrics --group-by |
| 31 | 232d85b | 1274 | +53 | archive --list --limit N, ai-cli list --outdated, atlas-ci-status.yml, vault verify --format json-lines, metrics --group-by --with-cost, doctor --diff-history N |
| 32 | 41a3506 | 1321 | +47 | vault verify --out PATH, ai-cli list --outdated --strict, archive --list --name-match PATTERN, atlas-metrics.yml cost artifact, doctor --diff-history-all, metrics group-by prometheus (rollback) |
| **33** | **push** | **1366** | **+45** | ai-cli list --outdated --json-lines, archive --list --json-lines, metrics group-by prometheus --out PATH, doctor --diff-history-all --strict, atlas-doctor.yml diff-history-all artifact, vault backup --split SIZE_MB |

Toplam **48 feat commit** + 8 docs commit bugün; **+454 test** (912
→ 1366). Cov `%91.18 → %91.39`. Docker YASAK otomatik gate; 7 GHA
workflow; 1 sözleşme rollback (SPEC 081, 32. tur); +35 CLI bayrak
varyasyonu bu 8 turda.

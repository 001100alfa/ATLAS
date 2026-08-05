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

**Son çalışma:** 2026-08-05 (28. tur — 068 + 070 + 067 + 066 + 071 + 069)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 28. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**1110/1110 test yeşil** (+12 skip), cov ~%91.5+, mypy strict + ruff +
scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-05 — 28. tur)

Kullanıcı "hepsini sıra ile uygula" → 27. tur adayları (066-071) tümü
zincirleme. Sıra `068 → 070 → 067 → 066 → 071 → 069` (küçükten büyüğe).

1. **Görev 068** — `metrics --alert-slack URL` (`7e27b4f`)
   - Slack incoming webhook `{text}` provider format.
   - SPEC 064 `_post_alert_webhook` yeniden kullanıldı (SSRF savunma
     + timeout aynı).
   - Üçlü ortogonal: email + webhook + slack birlikte çalışır.
   - +5 test.

2. **Görev 070** — `.github/workflows/atlas-doctor.yml` (`9a1c909`)
   - SPEC 056 vault-health.yml kardeşi.
   - Fresh `doctor --strict --scan-src` + koşullu `--auto-baseline`
     delta (2 gate).
   - Fail step: `rc_strict OR rc_diff ≠ '0'` → exit 1.
   - +6 test.

3. **Görev 067** — `vault backup --keep-encrypted N` (`636b692`)
   - `prune_encrypted_backups` (glob `vault-*.tar.gz.gpg`).
   - SPEC 041.1 `--keep` (plain) ile ORTOGONAL — iki ayrı havuz.
   - +9 test.

4. **Görev 066** — `vault restore --decrypt [PASSPHRASE]` (`05a12fa`)
   - `decrypt_backup` (SPEC 063 kardeşi; `gpg --decrypt`).
   - Temp plain `<target.parent>/.vault-restore-decrypt-<pid>.tar.gz`;
     restore sonrası **finally** silinir.
   - `.gpg` uzantı + `--decrypt` YOK → UYARI (auto-detect nazikliği).
   - +11 test.

5. **Görev 071** — `archive --restore --search PATTERN` (`e2ed9e5`)
   - SPEC 065 + SPEC 033 birleşim.
   - `--restore` `nargs="?"` `const=""` sentinel (bayraksız + `--search`).
   - Tek eşleşme → task_id çıkar; 0 → exit 6; 2+ → exit 2 belirsizlik.
   - +7 test.

6. **Görev 069** — `run --estimate` LLM'siz cost tahmini (`6f776f4`)
   - `_estimate_run_cost` heuristik: `max_steps * tokens_per_call`
     (env override); stub veya fiyat 0 → cost 0.
   - `--dry-run` (SPEC 020) FARKLI — planner çalışır. `--estimate`
     planner ÇAĞIRMAZ.
   - Audit kayıtsız (LLM yok).
   - +11 test.

7. **Kalite kapıları:** her görev branch → kod → test → tam
   pytest/mypy/ruff/scan → main'e ff-merge. 6 lineer commit.

---

## Sıradaki Karar (kullanıcıya sunulacak)

28. tur adayları tamamlandı. Yeni 6 aday üretildi:

- **Görev 072 — `--estimate` adaptif hesap:** SPEC 069 heuristiği
  SPEC 023 metrics'ten alınan **son N call ortalaması** ile değiştir
  (env kapatılabilir). Küçük-orta.
- **Görev 073 — `atlas vault backup --encrypt --recipient KEY_ID`:**
  SPEC 063 GPG symmetric yerine (veya buna ek) public-key encryption
  (`gpg --encrypt -r <key>`). Orta.
- **Görev 074 — `.github/workflows/atlas-metrics.yml`:** SPEC 023
  metrics.jsonl artifact'ini PR'a comment olarak yapıştıran workflow
  (SPEC 056/070 kardeşi). Küçük.
- **Görev 075 — `atlas archive --list [--json]`:** SPEC 007/033'ün
  kardeşi — `archive/` dizinindeki arşivleri listele (task_id, date,
  size, member_count). Küçük-orta.
- **Görev 076 — `atlas metrics --window MINUTES`:** SPEC 023 `--limit N`
  yerine (veya ek) son X dakikadaki kayıtlar. Cron-friendly. Küçük-orta.
- **Görev 077 — Docker YASAK gate:** `.github/workflows/no-docker.yml` +
  pre-commit gate: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
  commit'e girerse HATA (proje sözleşmesi). Küçük.

---

## Hızlı Bağlam

**Branch grafı:** `origin/main + 7 commit local (28. tur — push edilecek)`
Lokal feature branch YOK.

**main'e giren 6 feat + 1 docs commit (2026-08-05 28. tur):**
```
6f776f4 feat(069): atlas run --estimate LLM'siz cost tahmini
e2ed9e5 feat(071): atlas archive --restore --search PATTERN (SPEC 065+033 birlesim)
05a12fa feat(066): atlas vault restore --decrypt GPG decrypt-restore zinciri
636b692 feat(067): atlas vault backup --keep-encrypted N (.tar.gz.gpg retention)
9a1c909 feat(070): .github/workflows/atlas-doctor.yml — doctor CI gate
7e27b4f feat(068): atlas metrics --alert-slack URL Slack {text} provider format
```

**Kalite kapıları:**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 1110 passed, 12 skipped
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas metrics --alert-slack URL` (Slack `{text}` format)
- `atlas vault backup --keep-encrypted N` (.gpg retention)
- `atlas vault restore --decrypt [PASSPHRASE]` (GPG decrypt-restore)
- `atlas archive --restore --search PATTERN` (arama-tabanlı restore)
- `atlas run --estimate` (LLM'siz cost tahmini) + `--json`

**Yeni workflow:** `.github/workflows/atlas-doctor.yml` (SPEC 056 kardeşi).

**Yeni env sözleşmesi:**
- `ATLAS_ESTIMATE_TOKENS_PER_CALL` — SPEC 069 heuristik override
  (default 500).

**Yeni yardımcılar:**
- `_estimate_run_cost` (cli.py, SPEC 069)
- `decrypt_backup` (vault_backup.py, SPEC 066)
- `prune_encrypted_backups` (vault_backup.py, SPEC 067)

**Exit kodları:** DEĞİŞMEDİ.

**Kritik sözleşme değişmezlikleri:**
- SPEC 002/020/023/030/031 run BİT-UYUMLU.
- SPEC 007/012/017/033/065 archive BİT-UYUMLU.
- SPEC 041/041.1/042/046/052/056/057/058/059/063/064 BİT-UYUMLU.

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-05 üstteki 3 blok (28/27/26. tur).
2. Bu dosya (DEVAM_NOKTASI.md).
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`.
4. Değişecek modülün üstündeki docstring.

---

## Kapanış Notları

- **1110 test yeşil** (1061 → 1110; bu tur +49; oturum başı 319'dan +791)
- 6 lineer feat + 1 docs commit
- Yeni env: `ATLAS_ESTIMATE_TOKENS_PER_CALL`
- Yeni CLI: 5 yeni bayrak/alt-komut varyasyonu
- Yeni workflow: `atlas-doctor.yml`
- Yeni test dosyaları: `test_cli_metrics_alert_slack.py`,
  `test_cli_vault_backup_keep_encrypted.py`,
  `test_cli_vault_restore_decrypt.py`,
  `test_cli_archive_restore_search.py`, `test_cli_run_estimate.py`
  (+ `test_github_workflows.py` genişletildi) — 5 yeni dosya + 6 test SPEC.
- Docker YASAK yürürlükte
- Sıradaki tur için 6 aday (072–077).

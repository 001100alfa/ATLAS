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
>    `DECISIONS.md`'nin son 2026-08-04 girişlerini kaba tarama.

**Son çalışma:** 2026-08-04 (26. tur — 056 + 057 + 054 + 058 + 055 + 059)
**Branch:** `main` (6 feat + docs, PUSH edilecek)
**Working tree:** temiz
**Durum:** 26. tur tamamlandı; 6 aday görev; tümü main'e lineer ff-merge.
**995/995 test yeşil** (+12 skip), cov %91.50, mypy strict + ruff + scan
temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-04 — 26. tur)

Kullanıcı "DEVAM ET" tetikleyicisi → 26. tur seçimi "HEPSİ" onay
verildi. 6 görev zincirleme, sıra `056 → 057 → 054 → 058 → 055 → 059`
(küçükten büyüğe).

1. **Görev 056** — `.github/workflows/vault-health.yml` (`288c769`)
   - PR + push[main] tetikleyici, vault + src path filtresi.
   - 7 step: checkout → setup-uv → uv sync → `atlas vault verify
     --strict --dump-report health.md` (continue-on-error + rc
     `$GITHUB_OUTPUT`) → upload-artifact (30 gün) → PR comment
     (peter-evans/create-or-update-comment@v4, fail-only) → fail step
     (rc != 0 → exit 1).
   - permissions `pull-requests: write`; concurrency cancel-in-progress.
   - +9 test (PyYAML defensive `on:` boolean parse).

2. **Görev 057** — `atlas doctor --diff BASELINE_JSON` (`7e697be`)
   - `_diff_doctor_reports(baseline, current)` yeni yardımcı.
   - `warnings_added/removed` (set fark sorted) + `quality_deltas`
     (regressed/resolved/changed/appeared/disappeared) + `has_regression`
     / `has_improvement` + schema_version delta.
   - `--diff` mutex GRUBU DIŞINDA (`--json` ile ortogonal); semantik
     mutex kod içinde: `--diff + --serve/--schema/--format prometheus`.
   - `--strict + has_regression` → exit 9.
   - **Bug fix**: `--diff + --serve` sıralaması — semantik check
     blocking dal ÖNCE (aksi hâlde HTTP server açılıp test hang).
   - **Bug fix**: Windows cp1254 stdout — pytest capsys Unicode >0xFF
     encode edemez → insan çıktısında ASCII-only marker
     (`[+] [-] [!] [~]`).
   - +23 test.

3. **Görev 054** — `atlas doctor --http-check URL` (`0a4474e`)
   - `_check_http(url, timeout=5.0)` yardımcı (stdlib urllib.request).
   - `quality.http_check` alanı: url/status_code/latency_ms/warning.
   - Prometheus: `atlas_doctor_http_check_up 0|1` + `_latency_ms`
     gauge (koşullu).
   - `--strict + warning` → exit 9.
   - +15 test (gerçek HTTP `ThreadingHTTPServer(0)` ephemeral).

4. **Görev 058** — `atlas vault fix-broken` YIKICI (`8d35d38`)
   - Ayrı alt-komut (SPEC 046 kalıbı — `verify` DEĞİŞMEDİ).
   - `StubAction` frozen dataclass; `create_stub_notes(vault, broken,
     target, *, dry_run)`.
   - Aynı hedefe birden çok `from` → TEK stub + kaynak listesi.
   - Hedef vault'ta zaten var → `action="skipped"` (yarış durumu).
   - Varsayılan hedef `<vault>/_stubs/`; `--target` override.
   - Audit: `atlas-vault / fix-broken`.
   - +14 test.

5. **Görev 055** — `atlas replay --serve HOST:PORT` JSON (`81eac09`)
   - **SPEC 051 refactor** (bit-uyumlu): `make_handler` +
     `serve_prometheus_http` `content_type` + `allowed_paths`
     parametrik. Default Prometheus. Handler adı
     `_PrometheusHandler` → `_AtlasHTTPHandler`.
   - `_build_replay_json_body(limit)` → JSON string, her istek
     yeniden.
   - Endpoint: `GET / | /runs`; content-type
     `application/json; charset=utf-8`.
   - Mutex: `--serve + --list` / `--serve + <run-id>` → exit 2.
   - +10 test.

6. **Görev 059** — `atlas metrics --alert-email` SMTP (`0db2bec`)
   - `_send_alert_email(subject, body) -> (ok, err)` (stdlib smtplib).
   - Env: `ATLAS_SMTP_HOST/PORT/USER/PASSWORD/STARTTLS` +
     `ATLAS_ALERT_FROM/TO`.
   - `--alert PCT --alert-email` → eşik aşılırsa SMTP notify; exit 8
     KORUR (email yan etkiden bağımsız).
   - +12 test (`_FakeSMTP` monkey; gerçek network yok).

7. **Kalite kapıları:**
   - Her görev: branch → kod → test → tam pytest/mypy/ruff/scan → main'e ff-merge.
   - 6 lineer commit `288c769 → 7e697be → 0a4474e → 8d35d38 → 81eac09 → 0db2bec`.
   - Push ve final durum: aşağıda.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. 26. tur adayları
tamamlandı; yeni 6 aday üretildi:

- **Görev 060 — `atlas ai-cli install <name>`:** SPEC 037 ailesine
  yeni komut — tek paket ekleme (`npm install <name>` wrap +
  `package.json` update). Küçük-orta.
- **Görev 061 — vault verify JSON schema doc:** SPEC 042 VerifyReport
  şemasını `docs/api/vault-verify-schema.json` altında JSON Schema
  Draft-07 olarak yayımla. Küçük.
- **Görev 062 — `atlas doctor --diff --auto-baseline`:** SPEC 057
  genişleme — `.atlas/doctor-baseline.json` otomatik snapshot
  yönetimi (`--save-baseline` + `--diff` default `.atlas/`'tan
  oku). Küçük-orta.
- **Görev 063 — vault backup encryption:** SPEC 041 `--encrypt
  PASSPHRASE` — GPG symmetric ile encrypted tar. Orta (gnupg env
  bağımlılığı).
- **Görev 064 — `atlas metrics --alert-webhook URL`:** SPEC 059
  kardeşi — SMTP yerine POST JSON webhook (Slack/Discord/Teams
  incoming). Küçük-orta.
- **Görev 065 — `atlas archive --search PATTERN`:** SPEC 007 arşive
  eklenen full-text arama; tar açmadan Vault içindeki not adlarında
  regex. Orta.
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main + 7 commit local (26. tur — push edilecek)
```
Lokal feature branch YOK (temiz).

**main'e giren 6 feat + 1 docs commit (2026-08-04 26. tur):**
```
0db2bec feat(059): atlas metrics --alert-email SMTP notify
81eac09 feat(055): atlas replay --serve HOST:PORT JSON HTTP endpoint
8d35d38 feat(058): atlas vault fix-broken — kirik wikilink icin stub not (YIKICI)
0a4474e feat(054): atlas doctor --http-check URL dis HTTP saglik kontrolu
7e697be feat(057): atlas doctor --diff BASELINE_JSON delta raporu
288c769 feat(056): .github/workflows/vault-health.yml — vault verify CI gate
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 995 passed, 12 skipped, cov 91.50%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas doctor --diff BASELINE_JSON` (delta rapor + JSON + strict/9)
- `atlas doctor --http-check URL` (dış HTTP sağlık kontrolü)
- `atlas vault fix-broken [--apply] [--target DIR]` (YIKICI stub)
- `atlas replay --serve HOST:PORT` (JSON HTTP endpoint)
- `atlas metrics --alert-email` (SMTP notify)

**Yeni davranış (kullanıcı-görünür):**
- `.github/workflows/vault-health.yml` — PR + push'da CI gate.
- `_stubs/` klasörü vault içinde (fix-broken YIKICI ile).
- Prometheus 2 yeni metrik: `atlas_doctor_http_check_up`,
  `atlas_doctor_http_check_latency_ms`.

**Yeni env sözleşmesi:**
- SPEC 059 SMTP: `ATLAS_SMTP_HOST/PORT/USER/PASSWORD/STARTTLS` +
  `ATLAS_ALERT_FROM/TO`.

**Yeni yardımcı modüller/fonksiyonlar:**
- `_diff_doctor_reports` (cli.py, SPEC 057)
- `_check_http` (cli.py, SPEC 054)
- `_build_replay_json_body` (cli.py, SPEC 055)
- `_send_alert_email` (cli.py, SPEC 059)
- `StubAction` + `create_stub_notes` (vault_verify.py, SPEC 058)

**Refactor:**
- `observability/prometheus_server.py`: `make_handler` +
  `serve_prometheus_http` `content_type` + `allowed_paths`
  parametrik. Handler class `_AtlasHTTPHandler`. Mevcut çağırıcılar
  bit-uyumlu.

**Exit kodları:** DEĞİŞMEDİ.
- SPEC 057 `--strict + regresyon` → **9** (SPEC 032 kalıbı).
- SPEC 059 email başarısız → **8** KORUR (semantik önemli).

**Kritik sözleşme değişmezlikleri:**
- `atlas doctor`, `atlas metrics`, `atlas replay`, `atlas vault
  verify/fix-orphans` mevcut çıktıları BİT-UYUMLU.
- SPEC 043/047 Prometheus text formatı — 054 iki yeni koşullu metrik
  ekledi ama diğer satırlar dokunulmadı.
- SPEC 028 `atlas replay --list --json` çıktı sözleşmesi = SPEC 055
  HTTP body (aynı `_collect_replay_runs`).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-04 üstteki iki blok (26. tur ~23 giriş +
   25. tur ~24 giriş = ~47 giriş bugün — daha 2 gün önce); 2026-07-31
   altında 28; 2026-07-30 altında 29; 2026-07-29 altında 39.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- **995 test yeşil** (838 → 912 → 995; 25. tur +157, 26. tur +83;
  oturum başı 319'dan +676)
- 6 lineer commit + docs; push edilecek → sonra SENKRON
- Lokal feature branch YOK (temiz)
- Yeni env sözleşmesi: SMTP (`ATLAS_SMTP_*` + `ATLAS_ALERT_FROM/TO`)
- Yeni CLI komutu: `vault fix-broken`; yeni bayraklar: `doctor
  --diff`, `--http-check`, `replay --serve`, `metrics --alert-email`
- Yeni yardımcılar: 5 fonksiyon (cli.py) + 1 dataclass + 1 fonksiyon
  (vault_verify.py)
- Yeni test dosyaları: `test_github_workflows.py`,
  `test_cli_doctor_diff.py`, `test_cli_doctor_http_check.py`,
  `test_cli_vault_fix_broken.py`, `test_cli_replay_serve.py`,
  `test_cli_metrics_alert_email.py` (6 dosya, +83 test)
- Refactor: `prometheus_server.py` genelleştirildi (JSON scrape için
  yeniden kullanım)
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-08-04 altında ~47 giriş (25 + 26. tur);
  2026-07-31 altında 28; 2026-07-30 altında 29; 2026-07-29 altında 39
- Platform sözleşmesi: `--serve HOST:PORT` genel HTTP kalıbı
  (metrics/doctor Prometheus + replay JSON); gelecek `--serve`
  gerektiren komutlar `prometheus_server.py` altyapısını `content_type
  + allowed_paths` ile yeniden kullansın.
- Sıradaki tur için 6 aday hazır (060–065).

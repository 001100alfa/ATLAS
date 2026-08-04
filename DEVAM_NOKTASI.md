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

**Son çalışma:** 2026-08-04 (25. tur — housekeeping + 053 + 052 + 050 + 048 + 046 + 051)
**Branch:** `main` (7 lineer commit push edildi — SENKRON)
**Working tree:** temiz
**Durum:** 25. tur tamamlandı; 6 aday görev + housekeeping;
tümü main'e lineer ff-merge + push. **912/912 test yeşil**
(+12 skip), cov %91.18, mypy strict + ruff + scan temiz.

---

## Kullanıcıya kaldığı yerden başlatma

Yeni oturumda tek cümle yeter: **"devam et"**

---

## Bu turda yapılan (2026-08-04 — 25. tur)

Kullanıcı "DEVAM ET VE SIRA İLE HEPSİNİ YAP" komutu — 6 aday görevin
tamamı + housekeeping. Sıra: `chore → 053 → 052 → 050 → 048 → 046 → 051`.

0. **Housekeeping** — ai-cli bump commit'i (`173ea4e`)
   - 24. tur DIŞINDA oluşan `tools/ai-cli/package.json` bump'ı
     (`opencode-ai ^1.18.10 → ^1.18.11`) tekil `chore(ai-cli):` commit
     olarak temizlendi.

1. **Görev 053** — `atlas --version` / `-V` (`d5d877e`, micro)
   - `argparse.action="version"` parse_args'ta erken exit — subparser
     `required=True` olsa da çalışır.
   - Kaynak: `atlas_core.__version__` (pyproject.toml drift kontrolü
     test'te).
   - +4 test.

2. **Görev 052** — `vault verify --dump-report` + hook v3→v4 (`85e4db4`)
   - `format_report_markdown(report, vault_root)` UTC timestamp +
     koşullu bulgu bölümleri + Öneri.
   - `--dump-report PATH` yeni bayrak — verify çıktı sözleşmesi
     bit-uyumlu (yan etki dosya yazımı).
   - Hook v3→v4: `atlas vault verify --strict --dump-report
     .atlas/vault-health.md` gate; `.atlas/` git-ignored.
   - Yazma hatası SESSİZ (hook contextinde commit'i patlatmasın).
   - +9 test + 1 hook regression.

3. **Görev 050** — `atlas ai-cli update <name>` (`7fe8a05`)
   - `_run_npm_update(bin, dry_run, package=None)` keyword arg.
   - `update <name>` verilirse `dependencies` kontrolü (yoksa exit 2 +
     `atlas ai-cli list` önerisi); yoksa mevcut davranış (hepsi).
   - Konsol scope label: `[ai-cli] npm update (name) (source: bin)`.
   - +5 test; mevcut 27 test bit-uyumlu (3 mock lambda paralel güncellendi).

4. **Görev 048** — `tools/scheduling/` deployment templates (`92b633d`)
   - Linux (systemd --user): `.service` + `.timer` (03:00 UTC gunluk
     + jitter + Persistent) + `install-linux.sh` (sed placeholder).
   - Windows (Task Scheduler): v1.2 XML + `install-windows.ps1`
     (`[CmdletBinding()]` + Replace + UTF-16 temp XML + schtasks
     /Delete /F + /Create /XML).
   - `README.md` — kurulum + doğrulama + kaldırma.
   - +13 test (şablon bütünlüğü, XML parse, install script sözdizim).

5. **Görev 046** — `atlas vault fix-orphans` YIKICI alt-komut (`047e8bf`)
   - Yeni alt-komut (ana `verify` DEĞİŞMEDİ — bit-uyumlu).
   - Dry-run varsayılan; `--apply` yıkıcı `shutil.move`.
   - Hedef: `<vault>/_archive/orphans-YYYY-MM-DD/` (varsayılan) veya
     `--target DIR`.
   - Çakışma çözümü: `<name>-N.md` (1000 deneme koruması).
   - Alt-klasör orfanları (`daily/`, `tasks/`) `rglob` ile bulunur.
   - Audit: `atlas-vault / fix-orphans / '<N> not -> <target>'`.
   - +16 test.

6. **Görev 051** — `metrics/doctor --serve HOST:PORT` HTTP (`f4b5572`)
   - Yeni namespace `src/atlas_core/observability/`
   - `prometheus_server.py` stdlib `ThreadingHTTPServer` (dış
     bağımlılık YOK).
   - `parse_host_port`, `make_handler(body_fn)`, `serve_prometheus_http`.
   - Endpoint: `GET / | /metrics` → 200 text v0.0.4; diğerleri 404.
     `body_fn` exception → 500. Access log sessiz.
   - Her istek `body_fn()` yeniden çağırır (canlı scrape).
   - `--serve` metrics + doctor argparse mutex gruplarına eklendi.
   - `doctor --ping --serve` semantik exit 2 (her istek anthropic quota).
   - +26 test (7 birim + 6 HTTP + 3 CLI metrics + 4 CLI doctor +
     2 bit-uyumluluk); mevcut 91 test bit-uyumlu.

7. **Merge + kalite kapıları**
   - Her görev: branch → kod → test → tam pytest/mypy/ruff/scan →
     main'e ff-merge.
   - 7 commit lineer main'e: `173ea4e → d5d877e → 85e4db4 → 7fe8a05 →
     92b633d → 047e8bf → f4b5572`.
   - Push edildi; origin ↔ main SENKRON.

---

## Sıradaki Karar (kullanıcıya sunulacak)

**Yeni görev seçimi.** Pipeline'da açık iş yok. Doğal adaylar:

- **Görev 054 — `atlas doctor --http-check URL`:** eğer ATLAS dış bir
  HTTP servise (LLM proxy, MLflow, dashboard) bağlıysa, doctor bu
  URL'nin sağlığını raporda `quality.http_check` alanına ekler.
  Prometheus için: `atlas_doctor_http_check_up 0|1`. Küçük-orta.
- **Görev 055 — `atlas replay --run-id ID --serve`:** SPEC 028
  replay'i HTTP endpoint olarak yayımla (Prometheus DEĞİL, JSON):
  UI dashboard için. Orta.
- **Görev 056 — vault verify GitHub Actions template:**
  `.github/workflows/vault-health.yml` — PR'da vault verify --strict
  çalıştırıp bulguları PR comment'e yazan action. Küçük (workflow
  YAML + jq).
- **Görev 057 — `atlas doctor --diff`:** son 2 doctor JSON snapshot'ı
  arasındaki delta (yeni uyarılar, çözülmüş bulgular). CI regresyon
  için. Orta.
- **Görev 058 — `atlas vault verify --fix-broken`:** SPEC 046 orfan
  taşımanın kardeşi — kırık `[[wikilink]]`'leri stub not oluşturarak
  çözer (`--apply` gerekli). Orta.
- **Görev 059 — `atlas metrics --alert-email`:** SPEC 029 alert
  eşiğinde stderr yerine SMTP email. Orta (smtplib + credential env).
- Ya da başka öncelik varsa net söyle.

---

## Hızlı Bağlam

**Branch grafı:**
```
origin/main == main (f4b5572 + docs, SENKRON)
```
Lokal feature branch YOK (temiz).

**main'e giren 7 commit (2026-08-04 25. tur):**
```
f4b5572 feat(051): atlas metrics/doctor --serve HTTP scrape endpoint
047e8bf feat(046): atlas vault fix-orphans — orfan not arsivleme (YIKICI)
92b633d feat(048): tools/scheduling systemd + Task Scheduler sablonlari
7fe8a05 feat(050): atlas ai-cli update <name> tek paket guncelleme
85e4db4 feat(052): vault verify --dump-report + hook v3 -> v4 auto-dump
d5d877e feat(053): atlas --version / -V root bayragi
173ea4e chore(ai-cli): opencode-ai ^1.18.10 -> ^1.18.11 npm bump
```

**Kalite kapıları (bu turun sonu):**
```bash
uv run pytest -q --cov=atlas_core --cov=sections --cov-fail-under=90
# 912 passed, 12 skipped, cov 91.18%
uv run mypy src                # temiz (31 kaynak dosya)
uv run ruff check src tests    # temiz
uv run atlas scan src          # sır bulunamadı
```

**Yeni CLI davranışları (bu turda):**
- `atlas --version` / `-V` (yeni root bayrak)
- `atlas vault verify --dump-report PATH` (yeni bayrak)
- `atlas vault fix-orphans [--apply] [--target DIR]` (yeni alt-komut)
- `atlas ai-cli update <name>` (yeni positional)
- `atlas metrics --serve HOST:PORT` (yeni bayrak)
- `atlas doctor --serve HOST:PORT` (yeni bayrak)

**Yeni davranış (kullanıcı-görünür):**
- Pre-commit hook v3→v4: fail durumunda `.atlas/vault-health.md`
  auto-dump (kurulu v3 kullanıcıları `hooks install --force` şart).
- `tools/scheduling/` — Linux + Windows zamanlanmış görev şablonları.

**Yeni modüller:**
- `src/atlas_core/observability/__init__.py`
- `src/atlas_core/observability/prometheus_server.py`

**Env sözleşmesi:** DEĞİŞMEDİ.

**Exit kodları:** DEĞİŞMEDİ (mevcut 0/2/3/4/6/7/8/9 sınıfı korunur).
Yeni exit 2 nedenleri: `doctor --ping --serve` semantik mutex;
`ai-cli update <name>` deps'te yok; `--serve` geçersiz port.

**Kritik sözleşme değişmezlikleri (bu turda korundu):**
- `atlas metrics` mevcut çıktıları (bayraksız, `--json`, `--format
  prometheus`, `--alert`) BİT-UYUMLU.
- `atlas doctor` mevcut çıktıları (bayraksız, `--json`, `--schema`,
  `--format`, `--strict`, `--scan-src`, `--ping`, `--pretty`)
  BİT-UYUMLU.
- `atlas vault verify` (SPEC 042) BİT-UYUMLU — fix-orphans BAĞIMSIZ.
- `atlas ai-cli update` (name yok) BİT-UYUMLU — SPEC 037.1.
- `atlas hooks {install,uninstall,status}` BİT-UYUMLU.
- Prometheus text formatı (SPEC 043 + 047) BİT-UYUMLU — sadece
  transport eklendi (stdout ∪ HTTP).

**Bilinen flaky:** yok.

**Docker YASAK:** hâlâ yürürlükte.

**Görev-öncesi zorunlu okuma sırası:**
1. `DECISIONS.md` — 2026-08-04 üstteki 25. tur bloğu (bu tur ~24
   giriş); 2026-07-31 altında 28 giriş (23+24. tur); 2026-07-30
   altında 29; 2026-07-29 altında 39.
2. Bu dosya (DEVAM_NOKTASI.md)
3. Hedef görevin `pipeline/tasks/<XXX>/{00-need,09-ship}.md`
4. Değişecek modülün üstündeki docstring
5. `skills/engineering/prompt/SKILL.md` (LLM görevi hazırlarken)

---

## Kapanış Notları

- 912 test yeşil (838 → 912; bu tur +74; oturum başı 319'dan +593)
- 7 lineer commit + docs; origin ile SENKRON
- Lokal feature branch YOK (temiz)
- Yeni env YOK
- Yeni exit kodu YOK (mevcut sınıf korunur; yeni exit 2 nedenleri)
- Yeni CLI komutları: `vault fix-orphans` (yeni alt-komut);
  yeni bayraklar: `--version`, `-V`, `--dump-report`, `--serve`,
  `update <name>`
- Yeni modül: `src/atlas_core/observability/prometheus_server.py`
- Yeni test dosyaları: `test_cli_version.py`,
  `test_cli_vault_verify_dump.py`, `test_cli_ai_cli_update_single.py`,
  `test_scheduling_templates.py`, `test_cli_vault_fix_orphans.py`,
  `test_observability_prometheus_server.py`
- Hook şablonu v3 → v4 (mevcut kullanıcılar `hooks install --force`
  ile güncellemeli)
- Yeni deployment artefaktları: `tools/scheduling/` (systemd + Task
  Scheduler)
- Docker YASAK yürürlükte
- Portable bundle son sürüm: `D:\ATLAS.rar` (28 Temmuz, 1.9 GB)
- DECISIONS.md 2026-08-04 altında ~24 giriş; 2026-07-31 altında 28;
  2026-07-30 altında 29; 2026-07-29 altında 39 (toplam 120+)
- Platform sözleşmesi: Prometheus scrape endpoint ortak kalıbı
  (`metrics + doctor` `--serve HOST:PORT` mutex `--json/--format/
  --schema`); gelecek Prometheus tabanlı komutlar bu kalıbı takip etsin.
- Yeni namespace `atlas_core/utils/` (SPEC 049) + `atlas_core/
  observability/` (SPEC 051) — top-level yardımcı modüller için hazır.

# ATLAS Karar Günlüğü
Format: `## TARİH` altında madde; her madde [KARAR]/[VARSAYIM]/[HATA] etiketi taşır.

## 2026-04-16
- [KARAR] Çekirdek: Claude Code CLI + GitHub issue akışı.
- [KARAR] Paket yöneticisi: uv; yoksa pip'e düş.
- [KARAR] Ruff N806 sections/ için kapalı: EN 1993 gösterimi (Iy, Wel_y) proje standardı.
- [KARAR] Sayısal test politikası: analitik formüller rel_tol=1e-9; katalog karşılaştırması ayrı testte, tolerans gerekçeli.

## 2026-07-24
- [KARAR] Depo git ile başlatıldı (varsayılan branch: main). İlk commit tüm mevcut ağacı kapsar.
- [KARAR] Platform giriş noktası: `atlas` CLI (`atlas_core.cli:main`). Katmanları (GBrain/orchestrator/AuditLog/scan_secrets) uçtan uca bağlar; alt komutlar: context/remember/recall/run/audit-verify/scan.
- [KARAR] Vault ve audit yolları ATLAS_VAULT / ATLAS_AUDIT ortam değişkenleriyle geçersiz kılınır; audit çıktısı `.atlas/` gitignore'da.
- [KARAR] Geliştirme ortamı uv ile 3.12'ye bağlanır: `uv sync --extra dev` (`.venv` = 3.12.6). Sistem Python 3.11 kullanılmaz; makinede Python 3.12 mevcut ve uv onu bulur.
- [HATA] CLI çıktısı üstsimge birimleri (mm², mm⁴) içeriyordu; Windows konsolu (cp1254) bunları kodlayamayıp UnicodeEncodeError veriyordu. Düzeltme: her iki CLI `main()` başında `sys.stdout/stderr.reconfigure(encoding="utf-8")`. Kalıp: kullanıcıya yazan her çıktı akışı UTF-8'e sabitlenmeli.
- [KARAR] Taşınabilirlik: Python 3.12 + uv + çalışma bağımlılıkları projeye gömülü (`runtime/`, `vendor/wheels/`). Başlatıcılar `%~dp0` göreli, venv `--relocatable`. Offline kurulum `--no-index` ile ispatlandı (venv silinip yeniden kuruldu). İkili yük git'te tutulmaz (gitignore); `make-portable.cmd` üretir (online), `setup-portable.cmd` kurar (offline).
- [KARAR] AI çekirdek (Claude Code CLI) taşınabilirlik istisnasıdır: gömülmez, ayrı kurulur, çalışırken ağ ister. Hesap + platform CLI'ları tamamen offline çalışır. Bkz `docs/OFFLINE.md`.
- [HATA] `pip download numpy>=1.26` bash'te çalıştırıldığında `>` yönlendirme sanılıp `=1.26` boş dosyaları üretti. Kalıp: sürüm kısıtlı paket adlarını bash'te tırnak içine al veya `.cmd` içinde çalıştır (make-portable.cmd böyle).
- [KARAR] Çok-platform bundle: `tools/make_portable.py` (stdlib-only) windows/linux/macos-arm/x64 için `dist/atlas-<hedef>/` üretir. Yorumlayıcı arşivi host'ta AÇILMAZ (Windows'ta yabancı arşiv extract çok yavaş — Defender); `runtime/python.tar.gz` kopyalanır, hedefte native tar açar. Böylece tüm platformlar tek Windows host'tan üretilir. Sürüm sabitleri script başında (PY_VERSION, PBS_TAG).
- [HATA] `setup-portable.cmd` içinde düz `tar`, PATH'te Git'in GNU tar'ı varsa `C:\...` yolundaki `:`'i "uzak host" sanıp patlıyor. Düzeltme: Windows built-in bsdtar'ı açıkça çağır (`%SystemRoot%\System32\tar.exe`). Linux/macOS'ta sorun yok (drive-colon yok). Windows bundle sıfır-kurulumdan uçtan uca doğrulandı (izole kopya → setup → launcher, gömülü yorumlayıcıyla).

## 2026-07-24 (Juggler entegrasyonu)
- [KARAR] Web UI + masaüstü GUI = Juggler (juggler-ai/juggler). Entegrasyon = Juggler eklentisi (`integrations/juggler/`, Apache-2.0 — SDK ile aynı, ATLAS'a copyleft bulaşmaz). Juggler çekirdeği AGPL-3.0 ama ayrı derlenir/çalışır (bundle'a gömülmez). Yetenekler: `atlas_section`/`atlas_recall` context-item araçları, `/atlas-section` komutu, sistem-prompt katkısı; ATLAS launcher'larına `juggler/ops` shell köprüsü (PATH'ten).
- [KARAR] Eklentinin stabil sözleşmesi için `atlas-sections --json` eklendi (properties+units, hata JSON'u stderr/exit 2). Metin parse'a bağımlılık = kırılganlık.
- [KARAR] Yedek AI CLI'ları: OpenCode (`opencode-ai`) + Kilo (`@kilocode/cli`) proje-yerel npm kurulumu (`tools/ai-cli/`, `setup-ai-cli.cmd`), Claude Code limitinde/tercihe göre. Config/data proje içine hapsedilir; kullanıcı home'una dokunulmaz. Başlatıcılar `opencode_Run.cmd`/`kilo_Run.cmd`. node_modules+home gitignore, package(-lock).json tutulur.
- [KARAR] **Juggler ACP Agents (5 yedek ajan)** — v0.4.1. opencode/kilo/cline (npm), kimi (pip `tools/ai-cli/py-venv`), goose (Windows binary `tools/goose/` v1.44.0). Hepsi stdio ACP handshake ile doğrulandı (opencode 1.18.4, kilo 7.4.15, cline 3.0.46, kimi 1.49.0, goose 1.44.0).
  - **Spawn sözleşmesi:** Juggler ajanı `exec.LookPath(command)` + doğrudan `exec.Command` ile başlatır (KABUK YOK) ve env'i parent+config merge eder. Bu yüzden: Node CLI'lar `command:"node" args:[<bin>,...]` (`.cmd` shim'i PE değil, bare ad PATH'te yok); derlenmiş/Python ikilileri mutlak `.exe` yolu; her ajan için env ile config/data proje-yerele yönlendirilir (kullanıcı home'una dokunulmaz).
  - **Üretim:** `tools/gen-acp-config.js` `<project>/.juggler/acp.json`'u varlık-kontrollü yazar (yalnız kurulu ajan); `setup-ai-cli.cmd` üç ekosistemi kurar; `setup-acp-agents.cmd` config'i üretir. acp.json makineye özel → gitignore (goose/py-venv de); generator tutulur.
  - **Tuzaklar:** (a) goose zip'i bsdtar/PowerShell açamaz (`-5` / corrupt 244M → segfault) → **Python `zipfile`** ile aç, indirme TAM bitince. (b) Kimi `printf | kimi acp` EOF ile ölür → doğrulama stdin'i açık tutmalı (Juggler zaten tutar). (c) Node CLI'ları shim yerine node ile çağır.
- [HATA] Kilo Windows'ta `XDG_*` değişkenlerini onurlandırmıyor — `$HOME` köklü (`~/.config/kilo`) yollar kullanıyor; ayrıca npm `.cmd` shim'i (`endLocal &`) parent'ta set edilen `USERPROFILE`'ı yutuyor. Çözüm: `kilo_Run.cmd` node'u DOĞRUDAN çağırır (shim'i atlar) + `HOME`/`USERPROFILE`/`HOMEDRIVE`/`HOMEPATH`'i proje-yerele set eder. OpenCode ise Windows'ta da `XDG_*` (4'lü) onurlandırır — sorunsuz. İkisi de proje-içine yazacak şekilde doğrulandı (gerçek home Jul-20 opencode dizini dokunulmadı).
- [HATA] Juggler kaynaktan derleme Windows engelleri: (1) shallow clone submodule almaz — `3rdparty/wails` SSH URL'li, HTTPS rewrite gerekti (`-c url.https://github.com/.insteadOf=git@github.com:`); (2) submodule checkout MAX_PATH(260) aşımı — `core.longpaths=true`; (3) `//go:embed icon.png` — `assets/icons/juggler-icon.png`'yi `cmd/juggler/app/icon.png`'ye kopyala; (4) `ext link` symlink Windows'ta Developer Mode/admin ister — alternatif kopyalama. Headless `cmd/juggler` CGO'suz derlenir (CGO'lu dosyalar yalnız darwin). Go 1.26.5 ile derlendi, `ext validate` geçti, sunucu localhost:3939'da açıldı.

## 2026-07-24 (kalite sertleştirme — v0.4.2)
- [HATA] CI kalite kapısı delikleri (öz-inceleme): mypy yalnız `src/sections`'ı, coverage yalnız `--cov=sections`'ı görüyordu → `atlas_core` (platform katmanı) tip-kontrol/kapsam DIŞINDA. Düzeltme: CI `mypy src` + `--cov=sections --cov=atlas_core --cov-fail-under=90` (toplam %96).
- [KARAR] CI çift-OS: `quality` (ubuntu; ruff, mypy, JS `node --check`+`node --test`, `atlas scan` sır taraması, pytest+coverage) + `test-windows` (windows-latest; pytest regresyon). Windows-öncelikli özellikler için Windows leg zorunlu.
- [KARAR] `.gitattributes` çapraz-platform satır-sonu sözleşmesi: `.cmd/.bat/.ps1`=CRLF, `.sh`=LF (CRLF olursa bash "bad interpreter"), kaynak/doküman=LF, `.webp/.png/.exe/.zip`=binary. Bunsuz `.sh` bozulma riski.
- [KARAR] Manuel-doğrulanan araçlara regresyon testi: `make_portable.py` (pytest, saf mantık — ağ/subprocess yok) ve `gen-acp-config.js` (`node --test`, sahte projectRoot + stub bin). CI'da zorlanır. Test tuzağı: ESM'de yol için `fileURLToPath` (Windows `.pathname` `/C:/` verir); `node --test` dizin yerine glob (`*.test.mjs`) ile çağrılır.
- [KARAR] Atıl `api` extra (fastapi/uvicorn) kaldırıldı — hiçbir kod/CI kullanmıyordu; API desk (skills/trading) gelince geri tanımlanacak. `docs/CONTRIBUTING.md` GitHub'ca otomatik algılandığı için (root/.github/docs) taşınmadı.

# Changelog
Format: Keep a Changelog / SemVer.
Kararların gerekçeleri ve tuzaklar: [`DECISIONS.md`](DECISIONS.md).

## [0.4.2] - 2026-07-24
### Eklendi
- Otomatik testler: `tests/test_make_portable.py` (10) ve
  `tests/juggler/gen-acp-config.test.mjs` (`node --test`, 4) — daha önce yalnız
  manuel doğrulanan araçlara regresyon koruması.
- `SECURITY.md` (sır/audit/bildirim politikası), `docs/adr/` (ADR referansı gerçek),
  `.gitattributes` (satır-sonu: `.cmd`=CRLF, `.sh`=LF; ikili dosyalar).
### Düzeltildi (kalite kapıları — öz-inceleme)
- CI mypy artık **tüm `src`** (atlas_core dahil), yalnız `sections` değil.
- CI coverage `--cov=sections --cov=atlas_core` (platform katmanı da ölçülür, %96).
- **Windows test job'u** eklendi (çift-OS matrix); JS `node --check` + `node --test`
  ve `atlas scan` (sır taraması) CI adımları.
- README stale "37 test" → 39; atıl `api` extra (fastapi/uvicorn) kaldırıldı.

## [0.4.1] - 2026-07-24
### Eklendi
- Juggler **ACP Agents** entegrasyonu — 5 yedek AI kodlama ajanı stdio ACP
  (Agent Client Protocol) üzerinden model olarak sürülebilir:
  opencode, kilo, cline (npm), kimi (pip), goose (Windows binary).
  `setup-ai-cli.cmd` üçünü de kurar; `setup-acp-agents.cmd` +
  `tools/gen-acp-config.js` `<project>/.juggler/acp.json` üretir (varlık-kontrollü).
### Düzeltildi
- ACP Agents panelinde kilo/opencode çalışmıyordu: Juggler ajanı
  `LookPath(command)`+`exec` ile spawn eder (kabuk yok) — `command:"kilo"`
  PATH'te yok, `.cmd` shim'i PE değil. Doğru kayıt: Node CLI'lar `command:"node"`,
  derlenmiş/Python ikilileri mutlak exe yolu; env ile config/data proje-yerel.
- cline/goose/kimi ACP panelinde çalışmıyordu: kurulu değillerdi — portable
  kuruldu ve stdio ACP handshake ile doğrulandı (cline 3.0.46, goose 1.44.0,
  kimi 1.49.0).
### Diğer
- `docs/AI-CLI.md` ACP bölümü; goose python-zipfile ile açılır (bsdtar bozuyordu).

## [0.4.0] - 2026-07-24
### Eklendi
- Juggler entegrasyonu — web UI + masaüstü GUI ön-yüzü ([`docs/JUGGLER.md`]):
  - `integrations/juggler/` eklentisi (Apache-2.0): `atlas_section` ve
    `atlas_recall` context-item araçları, `/atlas-section` slash komutu,
    sistem-prompt katkısı; ATLAS launcher'larına `juggler/ops` shell köprüsü.
  - Başlatıcılar: `juggler-webui_Run/Close.bat`, `juggler-desktop_Run/Close.bat`.
  - `atlas-sections --json` (properties + units; hata JSON'u stderr, exit 2).
- Taşınabilir yedek AI CLI'ları (Claude Code limitinde/tercihe göre):
  OpenCode (`opencode-ai`) + Kilo (`@kilocode/cli`), proje-yerel npm kurulumu
  (`setup-ai-cli.cmd`), `opencode_Run.cmd` / `kilo_Run.cmd`. Config/data proje
  içine hapsedilir (OpenCode XDG_* 4'lü; Kilo HOME override). [`docs/AI-CLI.md`].
- MIT lisansı (`LICENSE`) + README rozetleri (CI, Python, sürüm, ruff, mypy, MIT).
### Düzeltildi
- `setup-portable` (ve Juggler setup) Windows'ta built-in bsdtar'ı açıkça çağırır.
- Kilo Windows'ta XDG_* onurlandırmıyor + npm `.cmd` shim'i USERPROFILE'ı yutuyor
  → `kilo_Run.cmd` node'u doğrudan çağırır + HOME/USERPROFILE proje-yerele.
### Diğer
- Depo yayımlandı: https://github.com/001100alfa/ATLAS (public, MIT, CI yeşil).

## [0.3.0] - 2026-07-24
### Eklendi
- Taşınabilir / çevrimdışı çalışma-zamanı: gömülü Python 3.12 + uv +
  bağımlılıklar (`runtime/`, `vendor/wheels/`); göreli başlatıcılar
  (`atlas.cmd`, `atlas-sections.cmd`); `setup-portable.cmd` (offline,
  `--no-index`), `make-portable.cmd` (üretici).
- Çok-platform bundle üreticisi `tools/make_portable.py` (stdlib-only):
  windows/linux/macos-arm/macos-x64 için `dist/atlas-<hedef>/` altında
  bağımsız kopyala-çalıştır ağaçlar. Yorumlayıcı arşivi hedefte native
  `tar` ile açılır; wheel'ler platforma özel çekilir.
- Platform giriş noktası `atlas` CLI (`atlas_core.cli`): context/remember/
  recall/run/audit-verify/scan — beyin+orkestratör+güvenlik uçtan uca.
- `docs/OFFLINE.md`, `docs/THIRD_PARTY_LICENSES.md`.
### Düzeltildi
- CLI çıktısı Windows konsolunda (cp1254) üstsimge birimlerde
  (mm², mm⁴) UnicodeEncodeError veriyordu → stdout/stderr UTF-8'e sabitlendi.
- `setup-portable` Windows'ta built-in bsdtar'ı açıkça çağırıyor
  (PATH'teki GNU tar `C:\` yolunu uzak-host sanıyordu).
### Diğer
- Depo git ile başlatıldı (main); geliştirme akışı uv'ye taşındı.

## [0.2.0] - 2026-04-16
### Eklendi
- GBrain: birleşik hafıza arayüzü (remember/recall/context_for;
  anahtar kelime + graf-komşuluğu skorlaması).
- atlas_core platformu: beyin (Obsidian vault + wikilink graf),
  arşiv, güvenlik (hash-zincirli audit + sır tarayıcı),
  orkestratör (registry + bütçeli çağrı + P-A-O-R döngüsü),
  YAML workflow motoru (gstack).
- security-auditor ve orchestrator subagent'ları; vault başlangıç grafı.

## [0.1.0] - 2026-04-16
### Eklendi
- `sections` paketi: kaynaklı I-kesit ve kutu kesit özellikleri
  (A, Iy, Iz, Wel, Wpl, kg/m), EN 1993 gösterimi, SI-mm.
- `atlas-sections` CLI.
- Ajan altyapısı: 5 komut, 3 subagent, 2 skill, hooks, CI.

[0.4.2]: https://github.com/001100alfa/ATLAS/releases/tag/v0.4.2
[0.4.1]: https://github.com/001100alfa/ATLAS/releases/tag/v0.4.1
[0.4.0]: https://github.com/001100alfa/ATLAS/releases/tag/v0.4.0
[0.3.0]: https://github.com/001100alfa/ATLAS/releases/tag/v0.3.0

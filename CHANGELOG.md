# Changelog
Format: Keep a Changelog / SemVer.

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

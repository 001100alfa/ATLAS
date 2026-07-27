# ATLAS Mimari

## Katmanlar
1. **Arayüz katmanı** (ön-yüz): kullanıcı ATLAS'a nereden erişir.
   - **AI çekirdek:** Claude Code CLI (`.claude/` davranışıyla). Limit
     aşımında/tercihe göre yedekler: **OpenCode** ve **Kilo** taşınabilir
     CLI'ları (`opencode_Run.cmd` / `kilo_Run.cmd`, bkz `docs/AI-CLI.md`).
   - **Web UI + masaüstü GUI:** **Juggler** ajan workbench'i Claude Code'u
     sürer; ATLAS yetenekleri `juggler-profile/` eklentisiyle taşınır
     (`atlas_section`, `atlas_recall`, `/atlas-section`). Bkz `docs/JUGGLER.md`.
2. **Ajan katmanı** (`.claude/`): Claude Code davranışı — CLAUDE.md talimat,
   commands/ iş akışları, agents/ uzman roller, settings.json izin + hooks.
3. **Bilgi katmanı** (`skills/`): alan kuralları. Ajan göreve başlamadan ilgili
   SKILL.md'yi okur — halüsinasyon yerine kayıtlı kural.
4. **Platform katmanı** (`src/atlas_core/`): ajan çalışma-zamanı çekirdeği.
   - **GBrain** (`memory/`): Obsidian-uyumlu vault + wikilink grafı; remember/
     recall/context_for. `atlas` CLI ile erişilir.
   - **Orkestratör** (`orchestrator/`): kayıtlı ajan + bütçeli çağrı + P-A-O-R
     döngüsü.
   - **Güvenlik** (`security/`): hash-zincirli audit log + sır tarayıcı.
   - **Workflow** (`workflows/`): YAML adım motoru.
   - Giriş noktası: `atlas` CLI (`atlas_core.cli`) — context/remember/recall/
     run/audit-verify/scan.
5. **Kod katmanı** (`src/sections/`): doğrulanmış mühendislik kütüphanesi.
   src-layout, pyproject ile paketlenir; `atlas-sections` CLI (`--json` dahil).
6. **Doğrulama katmanı** (`tests/` + CI): her sayısal fonksiyon el hesabı
   referansıyla test edilir (rel_tol=1e-9 analitik; katalog karşılaştırmalarında
   %2-3 tolerans + gerekçe). CI: ruff + mypy `--strict` + pytest.

## Taşınabilirlik / çevrimdışı
Python 3.12 + uv + çalışma bağımlılıkları projeye gömülüdür (`runtime/`,
`vendor/wheels/`); göreli başlatıcılar (`atlas.cmd`, `atlas-sections.cmd`).
`tools/make_portable.py` windows/linux/macos için bağımsız `dist/atlas-<hedef>/`
bundle'ları üretir (yorumlayıcı hedefte native `tar` ile açılır). AI çekirdek
(Claude Code) ve Juggler ağ gerektiren istisnalardır; hesap + platform CLI'ları
tamamen çevrimdışı çalışır. Bkz `docs/OFFLINE.md`.

## Veri akışı (bir görevin yaşamı)
GitHub issue → /gorev N → skill okuma → GBrain context_for → branch →
kod+test → tester subagent → reviewer subagent → PR → CI (ruff+mypy+pytest) →
merge → GBrain remember + vault.daily.

## Lisans sınırları
ATLAS: MIT. Juggler eklentisi: Apache-2.0 (SDK ile aynı, copyleft yok).
Juggler çekirdeği AGPL-3.0 — ayrı uygulama, birlikte dağıtılmaz. Gömülü
çalışma-zamanı bileşenleri: `docs/THIRD_PARTY_LICENSES.md`.

## Karar kaydı
Mimari kararlar DECISIONS.md'de [KARAR] etiketiyle tutulur; büyük kararlar için
docs/adr/ altına ADR dosyası açılır.

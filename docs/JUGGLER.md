# Juggler — ATLAS Web UI & Masaüstü GUI

[Juggler](https://github.com/juggler-ai/juggler) bir AI kodlama ajanı
workbench'idir: Go backend + Wails (masaüstü) + tarayıcı UI, ağaç-yapılı
oturumlar, JS eklenti mimarisi, çoklu-istemci. Model backend olarak **Claude
Code**'u sürebilir — böylece ATLAS'ın Claude Code çekirdeğine web UI ve masaüstü
GUI ön-yüzü olur. ATLAS yetenekleri Juggler'a `integrations/juggler/`
eklentisiyle taşınır.

## Lisans (önemli)
- **Juggler uygulama çekirdeği: AGPL-3.0.** Ayrı bir uygulamadır; ATLAS ile
  *birlikte dağıtılmadığı* sürece ATLAS'a copyleft yükümlülüğü taşımaz. Burada
  Juggler ayrı derlenip ayrı çalıştırılır (bundle'a gömülmez).
- **Juggler Extension SDK + bundled extensions: Apache-2.0.** ATLAS eklentisi
  (`integrations/juggler/`) bu yüzden Apache-2.0'dır ve copyleft yükümlülüğü yok.

## 1) Juggler'ı kaynaktan derle
Gereksinim: **Go 1.26+**, Wails v3 (repoda vendor'lu), `make`. Windows masaüstü
uygulaması için ek olarak WebView2 çalışma-zamanı gerekir.

```bash
git clone https://github.com/juggler-ai/juggler.git
cd juggler
make build          # juggler (headless sunucu) + juggler-app (masaüstü) + juggler-test
```

- **Headless sunucu** (`cmd/juggler`) — GUI'siz; başlatınca bağlantı URL'si +
  QR basar, tarayıcıdan bağlanılır. Windows'ta C derleyici gerektirmez
  (CGO'lu dosyalar yalnız macOS'a özgü). Yalnız bunu derlemek:
  ```bash
  go build -o juggler-server ./cmd/juggler
  ```
- **Masaüstü uygulaması** (`cmd/juggler-app`) — Wails penceresi; Linux masaüstü
  natif derlenmeli, Windows binary'leri `make build-windows` ile cross-compile
  edilir.

Ayrıntılı ön-koşullar: Juggler deposundaki `CONTRIBUTING.md`.

## 2) ATLAS'ı PATH'e ekle
Eklenti `atlas` ve `atlas-sections` launcher'larını PATH üzerinden çağırır.
ATLAS dizinini (veya taşınabilir bundle'ı) PATH'e ekle ve doğrula:
```bash
atlas-sections i --h 1000 --b 300 --tw 12 --tf 20 --json
```
JSON dönüyorsa köprü hazırdır. (`atlas-sections --json`, eklentinin bağlı olduğu
stabil sözleşmedir.)

## 3) ATLAS eklentisini yükle
Derlenen `juggler` ikilisiyle:
```bash
juggler ext validate <atlas>/integrations/juggler   # admission check
juggler ext link     <atlas>/integrations/juggler   # ~/.juggler/extensions'a symlink + hot-reload
```

> **Windows notu:** `ext link` symlink oluşturur; Windows'ta symlink için
> **Developer Mode** açık olmalı veya terminal **yönetici** çalışmalı (yoksa
> "A required privilege is not held" hatası). Alternatif — symlink yerine
> **kopyala** (hot-reload olmaz, ama çalışır):
> ```bash
> cp -r <atlas>/integrations/juggler ~/.juggler/extensions/atlas-engineering
> ```

Juggler'ı başlat (`juggler` → URL/QR) veya masaüstü uygulamasını aç; Ayarlar →
Extensions altında **ATLAS Engineering** görünür.

## Doğrulama durumu (bu makinede)
- Juggler **kaynaktan derlendi** (Go 1.26.5, `CGO_ENABLED=0` — Windows'ta C
  derleyici gerekmedi; `cmd/juggler` headless sunucu). Wails v3 submodule'ü
  `core.longpaths=true` + HTTPS rewrite ile alındı.
- Gerçek `juggler ext validate` **geçti**: *"✓ ATLAS Engineering (0.1.0) —
  @atlas/engineering, 2 capability glob(s), compatible with host engineApi 1.0.0"*.
- Sunucu ayağa kalktı (`http://localhost:3939`), WebView2 host + engine + istemci
  bağlandı; LLM sağlayıcıları arasında **`claudecode`** mevcut (ATLAS çekirdeği).
- Not: bir aracın (`atlas_section`) LLM üzerinden uçtan uca çağrılması, yapılandırılmış
  bir Claude Code backend'i ve etkileşimli oturum gerektirir — o adım kullanıcı
  tarafında yapılır.

## Yetenekler
| Yetenek | Tür | Ne yapar |
|---|---|---|
| `atlas_section` | Context Item (LLM aracı) | Çelik kesit özellikleri (EN 1993, SI-mm) |
| `atlas_recall` | Context Item (LLM aracı) | GBrain hafızasından bağlam/karar getirir |
| `/atlas-section` | Slash komut | LLM'siz hızlı hesap: `/atlas-section i 1000 300 12 20` |
| system-prompt | Prompt katkısı | Etkin araçları modele tanıtır |

Kaynak ve geliştirme notları: [`integrations/juggler/README.md`](../integrations/juggler/README.md).

## Mimari ilişki
```
Kullanıcı ──► Juggler (web UI / masaüstü GUI)
                 │  model backend
                 ▼
             Claude Code  ◄── ATLAS .claude/ (skills, commands, agents)
                 │  atlas_section / atlas_recall / /atlas-section
                 ▼
             ATLAS CLI (atlas, atlas-sections)  →  doğrulanmış hesap + GBrain
```
AI çekirdek (Claude Code) ATLAS'ın taşınabilirlik istisnasıdır; Juggler de ağ
gerektiren bir ön-yüzdür. ATLAS'ın hesap çekirdeği çevrimdışı çalışmaya devam eder.

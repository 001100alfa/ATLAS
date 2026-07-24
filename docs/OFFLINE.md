# Taşınabilirlik ve Çevrimdışı Çalışma

ATLAS **taşınabilir**dir: klasörü kopyala, çalıştır. Çalışma-zamanı
bağımlılıkları (Python yorumlayıcısı + paketler) proje klasörüne gömülüdür;
sistemde Python kurulu olması gerekmez.

## Ne gömülü, ne değil

| Bileşen | Durum | Konum |
|---|---|---|
| Python 3.12 (yorumlayıcı) | ✅ gömülü | `runtime/python/` |
| uv (paket yöneticisi) | ✅ gömülü | `runtime/uv.exe` |
| numpy, ezdxf, pyyaml (+ bağımlılıkları) | ✅ gömülü venv | `runtime/venv/` |
| Offline wheel deposu | ✅ gömülü | `vendor/wheels/` |
| **Claude Code CLI (AI çekirdek)** | ⚠️ **istisna** | dış gereksinim — aşağıya bak |

### İstisna: AI çekirdek (Claude Code CLI)
ATLAS'ın temel çekirdeği Claude Code CLI'dır (Node.js tabanlı bir LLM ajan
arayüzü). Bu, projeye gömülmez; ayrıca kurulur ve çalışırken Anthropic API'ye
ağ erişimi gerektirir. Bu **bilinçli bir esnetmedir**: hesap kütüphanesi ve
platform CLI'ı (`atlas`, `atlas-sections`) tamamen çevrimdışı çalışır; yalnız
ajan modu (`claude`) internet ister.

## Kullanım

### Klasörü kopyalayan kullanıcı (offline)
Klasörde `runtime/venv` zaten varsa doğrudan çalışır:
```bat
atlas-sections i --h 1000 --b 300 --tw 12 --tf 20
atlas run "hedef"
```
`runtime/venv` yoksa (veya bozulmuşsa) bir kez **çevrimdışı** kur:
```bat
setup-portable.cmd
```
Bu yalnızca `vendor/wheels`'ten kurar (`--no-index`), internet **gerekmez**.

### Git'ten klonlayan kullanıcı (bir kez online)
Büyük ikili yük (`runtime/`, `vendor/wheels/`) git'te tutulmaz. Bir kez
üret (internet gerekir), sonrası çevrimdışı:
```bat
make-portable.cmd     :: Python 3.12 + uv + wheelhouse indirir (online)
setup-portable.cmd    :: venv'i offline kurar
```

## Çok-platform bundle üretimi (bakımcı)
Kök klasördeki `runtime/` bundle'ı **Windows x64** içindir. Başka
platformlar için bağımsız bundle'lar üretilir:
```bash
python tools/make_portable.py            # tüm hedefler
python tools/make_portable.py --list     # hedefleri gör
# veya: make-portable.cmd / ./make-portable.sh
```
Hedefler: `windows-x86_64`, `linux-x86_64`, `macos-aarch64`, `macos-x86_64`.
Çıktı `dist/atlas-<hedef>/` — her biri bağımsız kopyala-çalıştır ağaç.

**Tasarım:** yorumlayıcı arşivi (python-build-standalone) build makinesinde
AÇILMAZ; `runtime/python.tar.gz` olarak kopyalanır. Hedef makinede
`setup-portable` kendi OS'unun native `tar`'ı ile açar (hızlı) + venv + offline
pip. Böylece Linux/macOS bundle'ları bir Windows makinesinde üretilebilir.
Wheel'ler `pip download --platform ... --only-binary=:all:` ile her hedefe özel
çekilir. Sürüm sabitleri `tools/make_portable.py` başındadır (`PY_VERSION`,
`PBS_TAG`).

Hedef makinede kurulum:
```bash
cd atlas-linux-x86_64 && ./setup-portable.sh && ./atlas-sections i --h 1000 --b 300 --tw 12 --tf 20
```

## Çevrimdışı doğrulama
`setup-portable.cmd` `--no-index` ile çalışır: PyPI'ye hiç bağlanmaz. Başlatıcılar
(`*.cmd`) yalnız `runtime/venv` içindeki gömülü yorumlayıcıyı kullanır; hiçbir
noktada `pip install` / ağ çağrısı yapılmaz.

## Taşınabilirlik notları
- Başlatıcılar `%~dp0` ile göreli çalışır — klasör herhangi bir yola taşınabilir.
- Gömülü venv `--relocatable` üretildi; yol değişse de bozulmaz.
- Yönetici hakkı gerekmez; her şey kullanıcı alanında.
- Temiz kaldırma: klasörü sil, iz kalmaz (sistemde değişiklik yok).

## Lisanslar
Gömülü üçüncü-taraf bileşenlerin lisansları: `docs/THIRD_PARTY_LICENSES.md`.

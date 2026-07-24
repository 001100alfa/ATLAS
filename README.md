# ATLAS — Otonom Mühendislik Ajanı

Claude Code CLI üzerinde çalışan, kodlama uzmanı, kendi ihtiyaçlarını
yöneten ajan altyapısı + doğrulanmış mühendislik hesap kütüphanesi.

[![CI](https://github.com/001100alfa/ATLAS/actions/workflows/ci.yml/badge.svg)](https://github.com/001100alfa/ATLAS/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
[![Version](https://img.shields.io/badge/version-0.4.2-informational)](https://github.com/001100alfa/ATLAS/releases/tag/v0.4.2)
![Lint: ruff](https://img.shields.io/badge/lint-ruff-261230)
![Types: mypy strict](https://img.shields.io/badge/types-mypy--strict-2a6db2)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Depo:** <https://github.com/001100alfa/ATLAS> — CI: main'de ruff + mypy `--strict` + pytest.
**Son sürüm:** [v0.4.2](https://github.com/001100alfa/ATLAS/releases/tag/v0.4.2) · [tüm sürümler](https://github.com/001100alfa/ATLAS/releases)

## Kurulum
Paket yöneticisi **uv** (proje standardı). Python 3.12 gerekir; uv
yoksa 3.12'yi kendisi indirir — sistemde ayrı kurulum gerekmez.

```bash
git clone <repo-url> && cd atlas
uv sync --extra dev      # .venv (3.12) + tüm bağımlılıklar
uv run pytest            # 39 test, referans değerlerle doğrulanmış
claude                   # ajanı başlat
```

uv yoksa (klasik akış):
```bash
python3.12 -m venv .venv && .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
```

### Taşınabilir / çevrimdışı çalışma
Python + bağımlılıklar projeye gömülüdür; sistemde Python gerekmez. Klasörü
kopyala, çalıştır:
```bat
setup-portable.cmd    :: bir kez, OFFLINE (venv yoksa)
atlas-sections i --h 1000 --b 300 --tw 12 --tf 20
```
Git'ten klonladıysan bundle'ı bir kez üret (online): `make-portable.cmd`.
AI çekirdek (Claude Code CLI) bir istisnadır — ayrı kurulur. Ayrıntı:
[`docs/OFFLINE.md`](docs/OFFLINE.md).

### v0.4.0 hazır bundle'ları
Her platform için bağımsız, kopyala-çalıştır bundle.
[Sürüm sayfasından](https://github.com/001100alfa/ATLAS/releases/tag/v0.4.0)
doğrudan indir (indir → aç → `setup-portable`):

| Platform | İndirme |
|---|---|
| Windows x64 | `atlas-windows-x86_64-v0.4.0.zip` |
| Linux x64 | `atlas-linux-x86_64-v0.4.0.tar.gz` |
| macOS (Apple Silicon) | `atlas-macos-aarch64-v0.4.0.tar.gz` |
| macOS (Intel) | `atlas-macos-x86_64-v0.4.0.tar.gz` |

Alternatif: `make-portable.cmd` / `./make-portable.sh` ile kendin üret
(çıktı `dist/atlas-<hedef>/`).

| Platform | Bundle | Kurulum (bir kez, offline) | Çalıştır |
|---|---|---|---|
| Windows x64 | `atlas-windows-x86_64` | `setup-portable.cmd` | `atlas-sections i --h 1000 ...` |
| Linux x64 | `atlas-linux-x86_64` | `./setup-portable.sh` | `./atlas-sections i --h 1000 ...` |
| macOS (Apple Silicon) | `atlas-macos-aarch64` | `./setup-portable.sh` | `./atlas-sections i --h 1000 ...` |
| macOS (Intel) | `atlas-macos-x86_64` | `./setup-portable.sh` | `./atlas-sections i --h 1000 ...` |

Her bundle gömülü Python 3.12 + mimariye özel offline wheel'ler içerir;
`setup-portable` yorumlayıcıyı native `tar` ile açar, venv kurar, bağımlılıkları
`--no-index` ile yükler. İnternet gerekmez.

## Web UI & Masaüstü GUI (Juggler)
Ön-yüz olarak [Juggler](https://github.com/juggler-ai/juggler) ajan
workbench'i kullanılır; ATLAS'ın Claude Code çekirdeğini web UI ve masaüstü
GUI'den sürer. ATLAS yetenekleri (`atlas_section`, `atlas_recall`,
`/atlas-section`) `integrations/juggler/` eklentisiyle (Apache-2.0) Juggler'a
taşınır. Kurulum, derleme ve lisans: [`docs/JUGGLER.md`](docs/JUGGLER.md).

<p align="center">
  <img src="docs/images/juggler-desktop-light.webp" alt="Juggler masaüstü — onay akışı ve diff (açık tema)" width="49%">
  <img src="docs/images/juggler-desktop-plan.webp" alt="Juggler masaüstü — çok-adımlı plan paneli (koyu tema)" width="49%">
  <br>
  <img src="docs/images/juggler-mobile-dark.webp" alt="Juggler mobil web UI (koyu tema)" width="30%">
</p>

<sub>Juggler ön-yüzü: masaüstü onay/diff akışı, çok-adımlı plan paneli ve mobil web UI. Görseller Juggler'a aittir.</sub>

## Yedek AI CLI'ları (Claude Code limitinde)
Claude Code limit aşımında veya tercihe göre taşınabilir yedek AI kodlama
ajanları proje içinde kullanılabilir. Config/data proje içine hapsedilir.
```bat
setup-ai-cli.cmd     :: bir kez — hepsini kur (npm + pip + goose binary)
opencode_Run.cmd     :: OpenCode (doğrudan CLI)
kilo_Run.cmd         :: Kilo (doğrudan CLI)
setup-acp-agents.cmd :: Juggler "ACP Agents" olarak kaydet
```

**Juggler ACP Agents** — 5 ajan stdio ACP üzerinden model olarak sürülür:

| Ajan | Ekosistem | ACP | Sürüm |
|---|---|---|---|
| opencode | npm (ikili) | `opencode acp` | 1.18.4 |
| kilo | npm (Node) | `kilo acp` | 7.4.15 |
| cline | npm (Node) | `cline --acp` | 3.0.46 |
| kimi | pip (Python) | `kimi acp` | 1.49.0 |
| goose | Windows binary | `goose acp` | 1.44.0 |

Ayrıntı: [`docs/AI-CLI.md`](docs/AI-CLI.md).

## Ajan komutları
| Komut | İşlev |
|---|---|
| `/gorev N` | GitHub issue N'i uçtan uca çöz (branch→kod→test→PR) |
| `/plan "..."` | Plan çıkar, uygulamaz |
| `/audit` | Öz-denetim: lint, test, sır taraması, birim kontrolü |
| `/ihtiyac` | Eksik bağımlılık/araç envanteri + kurulum |
| `/ozet` | DECISIONS.md + git durumundan 5 satır özet |

## Platform CLI (`atlas`)
Beyin + orkestratör + güvenlik katmanlarını uçtan uca bağlayan arayüz:
```bash
uv run atlas context "kesit hesabı"        # göreve bağlam paketi (GBrain)
uv run atlas remember kesit "..." --link EN1993 --tag hesap
uv run atlas recall "atalet momenti"       # graf komşuluğu skorlamalı geri çağırma
uv run atlas run "hedef"                    # bütçeli P-A-O-R döngüsü, audit'li
uv run atlas audit-verify                   # denetim zinciri bütünlüğü
uv run atlas scan src/                      # sır taraması (commit öncesi)
```
Yollar `ATLAS_VAULT` / `ATLAS_AUDIT` ortam değişkenleriyle geçersiz kılınır.

## Hesap kütüphanesi
```bash
uv run atlas-sections i --h 1000 --b 300 --tw 12 --tf 20   # kaynaklı I
uv run atlas-sections box --h 200 --b 300 --t 10           # kutu
```
Çıktı: A, Iy, Iz, Wel_y, Wel_z, Wpl_y, kg/m (SI-mm, EN 1993 gösterimi).

## Dokümantasyon
- `docs/ARCHITECTURE.md` — katmanlar ve görev yaşam döngüsü
- `docs/CONTRIBUTING.md` — katkı ve kalite kapıları
- `CHANGELOG.md` — sürüm geçmişi

## Lisans
[MIT](LICENSE) — Copyright (c) 2026 Serkan Acan.

Gömülü/entegre üçüncü taraf bileşenler ayrı lisanslara tabidir: Juggler çekirdeği
AGPL-3.0 (ayrı uygulama, [`docs/JUGGLER.md`](docs/JUGGLER.md)); taşınabilir
çalışma-zamanı bileşenleri [`docs/THIRD_PARTY_LICENSES.md`](docs/THIRD_PARTY_LICENSES.md).

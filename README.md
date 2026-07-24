# ATLAS — Otonom Mühendislik Ajanı

Claude Code CLI üzerinde çalışan, kodlama uzmanı, kendi ihtiyaçlarını
yöneten ajan altyapısı + doğrulanmış mühendislik hesap kütüphanesi.

[CI durumu main branch'te otomatik: ruff + mypy --strict + pytest/coverage≥90]

## Kurulum
Paket yöneticisi **uv** (proje standardı). Python 3.12 gerekir; uv
yoksa 3.12'yi kendisi indirir — sistemde ayrı kurulum gerekmez.

```bash
git clone <repo-url> && cd atlas
uv sync --extra dev      # .venv (3.12) + tüm bağımlılıklar
uv run pytest            # 37 test, referans değerlerle doğrulanmış
claude                   # ajanı başlat
```

uv yoksa (klasik akış):
```bash
python3.12 -m venv .venv && .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
```

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

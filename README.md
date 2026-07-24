# ATLAS — Otonom Mühendislik Ajanı

Claude Code CLI üzerinde çalışan, kodlama uzmanı, kendi ihtiyaçlarını
yöneten ajan altyapısı + doğrulanmış mühendislik hesap kütüphanesi.

[CI durumu main branch'te otomatik: ruff + mypy --strict + pytest/coverage≥90]

## Kurulum
```bash
gh auth login
git clone <repo-url> && cd atlas
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
pytest        # 11 test, referans değerlerle doğrulanmış
claude        # ajanı başlat
```

## Ajan komutları
| Komut | İşlev |
|---|---|
| `/gorev N` | GitHub issue N'i uçtan uca çöz (branch→kod→test→PR) |
| `/plan "..."` | Plan çıkar, uygulamaz |
| `/audit` | Öz-denetim: lint, test, sır taraması, birim kontrolü |
| `/ihtiyac` | Eksik bağımlılık/araç envanteri + kurulum |
| `/ozet` | DECISIONS.md + git durumundan 5 satır özet |

## Hesap kütüphanesi
```bash
atlas-sections i --h 1000 --b 300 --tw 12 --tf 20   # kaynaklı I
atlas-sections box --h 200 --b 300 --t 10           # kutu
```
Çıktı: A, Iy, Iz, Wel_y, Wel_z, Wpl_y, kg/m (SI-mm, EN 1993 gösterimi).

## Dokümantasyon
- `docs/ARCHITECTURE.md` — katmanlar ve görev yaşam döngüsü
- `docs/CONTRIBUTING.md` — katkı ve kalite kapıları
- `CHANGELOG.md` — sürüm geçmişi

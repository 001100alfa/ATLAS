# Üçüncü Taraf Lisansları

ATLAS taşınabilir bundle'ında gömülü bileşenler ve lisansları. Her bileşenin
tam lisans metni ilgili paketin dağıtımı içindedir (wheel/dizin).

## Çalışma-zamanı (gömülü, `runtime/` + `vendor/wheels/`)

| Bileşen | Sürüm | Lisans | Tam metin |
|---|---|---|---|
| CPython | 3.12.13 | PSF-2.0 | `runtime/python/**/LICENSE.txt` |
| uv | 0.11.20 | Apache-2.0 VEYA MIT | https://github.com/astral-sh/uv |
| numpy | 2.5.1 | BSD-3-Clause | wheel `*.dist-info/LICENSE*` |
| ezdxf | 1.4.4 | MIT | wheel `*.dist-info/LICENSE` |
| pyyaml | 6.0.3 | MIT | wheel `*.dist-info/LICENSE` |
| fonttools | 4.63.0 | MIT | ezdxf bağımlılığı |
| pyparsing | 3.3.2 | MIT | ezdxf bağımlılığı |
| typing-extensions | 4.16.0 | PSF-2.0 | ezdxf bağımlılığı |

## Geliştirme (gömülü değil, `uv sync --extra dev` ile çekilir)
pytest (MIT), pytest-cov (MIT), ruff (MIT), mypy (MIT), types-PyYAML (Apache-2.0).

## Not
- AI çekirdek **Claude Code CLI** bundle'a dahil değildir (ayrı kurulur);
  kendi lisans/koşullarına tabidir. Bkz `docs/OFFLINE.md`.
- Kurulu paketlerin güncel listesi: `runtime\uv.exe pip list --python runtime\venv`.

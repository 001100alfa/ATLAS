# Görev 053 — Teslim

`atlas --version` / `-V` root bayrağı.

## Uygulama

- `atlas_core/cli.py::main`: parser'a `add_argument("--version", "-V",
  action="version", version=f"atlas {_atlas_version}")` eklendi.
- Kaynak: `atlas_core.__version__` (mevcut sabit, pyproject.toml ile eş).

## Kanıtlar

- +4 test (`tests/test_cli_version.py`):
  - `--version` → `atlas 0.4.2` exit 0
  - `-V` kısa formu aynı çıktı
  - Drift kontrolü: `__version__` `pyproject.toml` version ile bit-uyumlu
  - `--help` çıktısı `--version` ve `-V` içerir
- 838 → **842 yeşil**, 12 skip, cov %90.91.
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Değişmeyen sözleşme

- Mevcut alt-komutların hepsi BİT-UYUMLU (parser'a yeni root bayrak
  eklendi; subparser yapısı dokunulmadı).
- `atlas --help` yalnız `--version -V` satırı eklendi.

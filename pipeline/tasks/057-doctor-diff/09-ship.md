# Görev 057 — Teslim

`atlas doctor --diff BASELINE_JSON` — snapshot deltası.

## Uygulama

- **`_diff_doctor_reports(baseline, current) -> dict`** (yeni):
  - warnings set farkı (sorted)
  - `quality_deltas`: her alan için change etiketi
  - `has_regression` / `has_improvement` özet bayrakları
  - schema_version baseline+current
- **`_cmd_doctor`**: yeni `--diff` dallanması. Baseline yok/bozuk/kök
  obje değil → exit 2. Delta hesaplanır. `--json` ile JSON çıktı,
  aksi hâlde insan format (ASCII-only marker'lar). `--strict +
  has_regression` → exit 9.
- **Parser**: `--diff` bayrağı **mutex GRUBU DIŞINDA** (`--json` ile
  ortogonal). Semantik mutex kod içinde: `--diff + --serve/--schema/
  --format prometheus` → exit 2.
- **Sıra düzeltmesi**: `--diff + --serve` semantik kontrolü
  `_cmd_doctor` içinde ÖNCE (--serve blocking dalından önce). Aksi
  hâlde HTTP server açılıp test hang oluyordu.

## Kanıtlar

- +23 test (`tests/test_cli_doctor_diff.py`):
  - **Birim (10)**: aynı rapor → boş delta / yeni uyarı → regresyon /
    çözülen uyarı → iyileşme / quality regressed/resolved/changed /
    appeared+disappeared / deterministik sıra / schema_version delta /
    warnings duplicate set farkı.
  - **CLI (13)**: dosya yok / bozuk JSON / kök obje değil / insan
    çıktısı (self-compare) / yeni uyarı görünür (COZULEN) / JSON şema /
    pretty indent / strict regresyon exit 9 / strict yoksa 0 or 9 /
    3 semantik mutex (serve/format/schema) / default bit-uyumlu.
- Mevcut 100+ doctor testi BİT-UYUMLU.
- 921 → **944 yeşil**, 12 skip, cov %91.18 → %91.19.
- `uv run mypy src` temiz (31 kaynak).
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- `atlas doctor --diff BASELINE_JSON` bayrağı.
- Yeni fonksiyon `_diff_doctor_reports` public-ish (test edilir).

## Değişmeyen sözleşme

- `atlas doctor` mevcut çıktıları (bayraksız, `--json`, `--schema`,
  `--format`, `--strict`, `--scan-src`, `--ping`, `--pretty`,
  `--serve`) BİT-UYUMLU.
- Prometheus text formatı (SPEC 043 + 047) BİT-UYUMLU — delta ayrı bir
  mode.
- Exit kodları: 2/9 sınıfı; yeni exit nedeni yok.

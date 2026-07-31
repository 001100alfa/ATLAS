# Görev 047 — Teslim

`atlas doctor --format prometheus` — sağlık kontrolü scrape edilebilir.

## Uygulama

- `atlas_core/cli.py`:
  - Yeni fonksiyon: `_doctor_report_to_prometheus(report) -> str`
    - Prometheus text v0.0.4 formatı; deterministik sıralama.
    - Zorunlu 2 metrik (`up`, `warnings_total`); koşullu quality label
      + scan_src detay metrikleri.
  - `_cmd_doctor` içinde yeni fmt branch: `--format prometheus`
    (schema kısa devresinden sonra, JSON'dan sonra, insan'dan önce).
    `--strict` format bağımsız çalışır (exit 9 kaldı).
  - Parser: `--json`, `--schema`, `--format` üçlüsü
    `add_mutually_exclusive_group()` içine alındı — argparse mutex.
    `store_true`/`store` davranışları KORUNDU.

## Kanıtlar

- +11 test (tests/test_cli_doctor_prometheus.py):
  - **Birim (5)**: `_doctor_report_to_prometheus` — up + warnings,
    warnings sayısı, quality label healthy 0/1, scan_src koşullu, dolu.
  - **CLI (6)**: temel çıktı, `--json` mutex, `--schema` mutex,
    `--json --schema` mutex (yeni bonus), default bit-uyumlu,
    `--format human` bit-uyumlu.
- Mevcut **100 doctor testi** bit-uyumlu:
  - `test_cli_doctor_strict.py` — SPEC 032 strict; SPEC 032.2
    scan_src; SPEC 032.4 schema_version; SPEC 032.5 pretty; SPEC 040
    --schema.
  - `test_doctor_gui.py` — 34 test (22. tur bakım).
  - `test_doctor_processes.py`.
- 827 → **838 yeşil**, 12 skip, cov %90.90.
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- `atlas doctor --format {human,prometheus}` bayrağı.
- Yeni metrikler (2 zorunlu + N quality label + 2 opsiyonel scan_src).

## Değişmeyen sözleşme

- `atlas doctor` (bayraksız) BİT-UYUMLU.
- `atlas doctor --json`, `--json --strict`, `--json --pretty` BİT-UYUMLU.
- `atlas doctor --schema`, `--schema --pretty` BİT-UYUMLU.
- `atlas doctor --strict`, `--scan-src`, `--ping` BİT-UYUMLU.
- Schema descriptor (SPEC 040) DEĞİŞMEDİ (Prometheus çıktısı ayrı
  format, schema tanımı sadece JSON şemasını açıklıyor).
- Doctor exit kodları: 0/9 (mevcut); 2 yalnız argparse mutex hatası.

# Görev 097 — Teslim

`atlas doctor --diff-history-all --strict`.

## Uygulama

- SPEC 091 blok sonunda: `--strict` + snapshot delta'da
  `has_regression=True` olan var → exit 9.
- stderr mesajı: "REGRESYON: --strict verildi, N snapshot'ta regresyon
  (date, date, ...)".
- Bilgi çıktısı (tablo/JSON) YİNE basılır; sadece exit code değişir.
- Tarihçe boş → SPEC 091 exit 2 önce (strict öncesi).
- `--strict` YOKSA SPEC 091 exit 0 (bit-uyumlu).

## Kanıt

- +7 test (`tests/test_cli_doctor_diff_history_all_strict.py`):
  - Temiz + strict → exit 0/9 (sistem env'e bağlı; sözleşme rc in {0,9}).
  - Snapshot aynı warnings → exit 0 (regresyon yok).
  - Regresyon varsa stderr detay + date listesi.
  - --strict YOK → exit 0 her zaman (bit-uyumlu).
  - --strict + --json ORTOGONAL (içerik AYNI, rc değişir).
  - Multi-snapshot herhangi regresyon → exit 9.
  - Tarihçe boş + strict → SPEC 091 exit 2 (strict öncesi).
- 1344 → **1351 yeşil** (+7), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 091 çıktı içeriği AYNI (tablo + JSON snapshots şeması).
- SPEC 057 delta şeması AYNI.
- Exit 9 kalıbı SPEC 032/057 --strict ile UYUMLU.

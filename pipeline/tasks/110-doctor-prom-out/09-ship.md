# Görev 110 — Teslim

`atlas doctor --diff-history-all --format prometheus --out PATH`.

## Uygulama

- `_cmd_doctor` başında (schema kısa devresinden sonra):
  `--out` + (`--diff-history-all yok` VEYA `--format != prometheus`)
  → SPEC HATASI exit 2.
- Prometheus dalında `--out PATH` → `parent.mkdir` + `write_text`
  (SPEC 096 kalıbı).
- Yazma hatası exit 2.
- `--strict` (SPEC 097) ORTOGONAL — exit 9 dosya yazıldıktan sonra.
- Parser: `--out PATH` metavar (doctor parser'ında yeni).

## Kanıt

- +8 test (`tests/test_cli_doctor_diff_history_all_prom_out.py`):
  - Dosya yazıldı, stdout Prometheus text basmaz.
  - Dosya içeriği stdout modu ile AYNI.
  - Parent auto-mkdir.
  - --out --diff-history-all yok → exit 2.
  - --out --format=json → argparse choices exit 2.
  - --out --strict + regresyon → rc in {0,9}, dosya yazılır.
  - --out tek başına → exit 2.
  - --out YOKSA SPEC 104 stdout AYNI.
- 1428 → **1436 yeşil** (+8), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 104: `--out` yoksa stdout Prometheus çıktısı AYNI.
- SPEC 091: pretty/JSON dalları AYNI (--format prometheus yoksa).
- SPEC 097: --strict exit 9 davranışı AYNI (dosya modunda da).

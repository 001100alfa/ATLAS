# Görev 164 — Teslim

`atlas archive --schema` JSON'a `sub_commands` alanı; `archive --list
--schema` mevcut şema ile bit-uyumlu.

## Uygulama
- SPEC 149 `archive_schema` JSON'a `sub_commands` alanı eklendi (SPEC
  032.4 alan-ekleme bit-uyumlu):
  - `list`:    `{exit_codes: ["0","2"], spec: "075", desc}`
  - `restore`: `{exit_codes: ["0","2","3","6"], spec: "033", desc}`
  - `search`:  `{exit_codes: ["0","2"], spec: "065", desc}`
  - `all`:     `{exit_codes: ["0","2"], spec: "012", desc}`
- Mevcut top_level (7 alan) + exit_codes (0/2/3/6 birleşik) +
  formats + notes DOKUNULMADI.
- Prometheus çıktısına `sub_commands` EKLENMEDİ (YAGNI — yeni metric
  aile gerekir, mevcut 4 metric aile sayısı korundu).
- `archive --list --schema` mevcut kısa devre --list öncesi çalışır
  (schema dispatcher birinci).
- notes: SPEC 164 satırı eklendi.

## Kanıt
- +8 test (`tests/test_cli_archive_list_schema.py`):
  - `sub_commands` alanı var (4 alt komut adı)
  - `list` exit_codes = ["0", "2"] + spec="075"
  - `restore` exit_codes = ["0", "2", "3", "6"] + spec="033"
  - `search`/`all` exit_codes = ["0", "2"]
  - `archive --list --schema` = `archive --schema` (bit-uyumlu)
  - `--pretty --list --schema` indent=2
  - Prometheus çıktısında sub_commands YOK + metric sayı 4
  - SPEC 149 mevcut top_level 7 alan + exit_codes AYNI
- archive schema/list regresyon 72 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 149 JSON şeması geriye uyumlu (yeni alan eklendi; mevcut alanlar AYNI).
- SPEC 151 Prometheus çıktısı AYNI (sub_commands YOK).
- SPEC 155 --out --gzip yolu AYNI.
- SPEC 007/012/033/065/071/075 archive normal komutları AYNI.

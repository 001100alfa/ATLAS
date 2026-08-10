# Görev 149 — Teslim

`atlas archive --schema [--pretty]`.

## Uygulama
- `_cmd_archive` başında `--schema` kısa devre (SPEC 040/136/146 kalıbı).
- Arşiv kökü gerekmez; JSON şema tanımı basılır.
- 7 top_level alan (SPEC 075 `_list_archive_entries` şeması AYNI).
- exit_codes 0/2/3/6; formats human/json/json-lines.
- notes: SPEC 079/085/093/105/108/127/133/138/149 referansları.
- Parser: `--schema` + `--pretty` eklendi.

## Kanıt
- +7 test (`tests/test_cli_archive_schema.py`).

## Değişmeyen sözleşme
- SPEC 007/012/033/065/071/075: archive normal davranışlar AYNI.

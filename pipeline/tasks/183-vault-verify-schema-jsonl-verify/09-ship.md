# Görev 183 — Teslim

`vault verify --schema --format json-lines --out --gzip` kanıt tamamlama
(SPEC 159 doctor kalıp simetrisi vault verify için).

## Envanter (canlı doğrulama)
- SPEC 172 kalıbı **tam uygulanmış** — `_cmd_vault_verify` --schema
  json-lines dalında `jl_out`/`jl_gzip` locale, auto-suffix .gz,
  gzip.open("wt"), MUTEX kontrolleri hepsi mevcut.
- Yeni CLI kodu YOK. Yalnız ek kanıt testleri (SPEC 159 kalıp simetrisi).

## Kanıt (yeni)
- +4 test (`tests/test_cli_vault_verify_schema_jsonl_verify.py`):
  1. Parent auto-mkdir (nested dizin, `mkdir(parents=True)` kalıbı).
  2. Zaten `.gz` uzantılı PATH → ikinci `.gz` eklenmez (idempotent
     suffix kalıbı).
  3. Stdout ↔ düz dosya satır-bazında eşitlik (bit-uyumluluk sıkı
     kanıt).
  4. `--gzip` `--out` olmadan hem `--gzip` hem `--out` err mesajında.
- SPEC 172 + 183 birlikte 13 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 087 vault verify normal --format json-lines (bulgu NDJSON) AYNI.
- SPEC 136 vault verify --schema JSON default AYNI.
- SPEC 140 vault verify --schema --format prometheus AYNI.
- SPEC 145 vault verify --schema prom --out --gzip AYNI.
- SPEC 172 mevcut 9 test etkilenmedi (ek kanıt paralel dosyada).

## Not (bu turdan öğrenilen kalıp)
Aynı doktrin SPEC 159'da (doctor) uygulandı: "atomik doktrin 'eksik
yok' durumunda BOŞ commit yerine kalıp simetrisi kanıt testleri ile
kapatılır". SPEC 183 bunun ikinci uygulaması — gelecek turlarda diğer
`--schema --format {json-lines,prometheus} --out --gzip` yollarına da
uygulanmalı (archive schema jsonl, metrics schema jsonl, ai-cli status
schema jsonl — mevcut ama bu edge testleri yok).

# Görev 159 — Teslim

`atlas doctor --schema --format prometheus --out --gzip` kanıt tamamlama.

## Envanter (canlı doğrulama)
- SPEC 134 kalıbı **tam uygulanmış** — `_cmd_doctor` --schema Prometheus
  dalında `schema_out` / `schema_gzip` locale değişkenleri, auto-suffix
  `.gz`, gzip.open("wt"), MUTEX kontrolleri hepsi mevcut.
- Yeni CLI kodu YOK. Yalnız ek kanıt testleri (SPEC 155/156 kalıp
  simetrisi).

## Kanıt (yeni)
- +4 test (`tests/test_cli_doctor_schema_prom_out_verify.py`):
  1. Parent auto-mkdir (nested dizin, `mkdir(parents=True)` kalıp
     doğrulaması).
  2. Zaten `.gz` uzantılı PATH → ikinci `.gz` eklenmez (idempotent
     suffix kalıbı).
  3. Stdout ↔ düz dosya satır-bazında eşitlik (bit-uyumluluk sıkı
     kanıt; SPEC 134'de gzip decompress ile vardı, düz dosya için
     de eklendi).
  4. `--gzip` `--out` olmadan hem `--gzip` hem `--out` err mesajında.
- SPEC 134 + 159 birlikte 11 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 128 stdout Prometheus AYNI (--out yoksa).
- SPEC 040 JSON AYNI (--format yoksa).
- SPEC 110/114 diff-history-all yolu AYNI (mutex önden kısa devre).
- SPEC 134 mevcut 7 test etkilenmedi (ek kanıt paralel dosyada).

# Görev 040 — İhtiyaç

`atlas doctor --json` çıktısı `schema_version: "1"` alanı ile geliyor
(SPEC 032.4). Ama JSON tüketicileri hangi alanların hangi tipte
olduğunu, hangi alan hangi SPEC'ten geldiğini metadata olarak bilmek
istiyor. Bunun için ayrı bir schema komutu.

## Kabul kriteri
- `atlas doctor --schema` → JSON şema tanımı basar; SAĞLIK KONTROLÜ
  YAPMAZ (dizinlere dokunmaz, IO'suz, idempotent).
- Şema: `{schema_version, top_level[], quality_fields[], exit_codes{},
  notes[]}`.
- `--pretty` ile birlikte `indent=2`.
- Diğer doctor bayrakları (`--strict`, `--ping`, `--scan-src`) `--schema`
  ile birleşmez — `--schema` verildiğinde kısa devre.
- Exit 0 sabit (bilgi komutu).

## Riskli
- Bakım yükü: `_doctor_schema_descriptor` ve `_collect_doctor_report`
  eş güncel tutulmalı — 09-ship.md'ye not.

# Görev 087 — İhtiyaç

SPEC 042 `vault verify --json` tek büyük JSON basar. Binlerce broken link
olan devasa vault'larda tek satır JSON belleğe/tail'e verim düşürür.
Streaming (newline-delimited) çıktı yok.

## Kabul

- `atlas vault verify --format {human,json,json-pretty,json-lines}`.
- Default `--format` YOK → SPEC 042 BİT-UYUMLU (mevcut `--json`/`--pretty`
  yolu).
- `--format` + `--json` VEYA `--format` + `--pretty` → MUTEX exit 2.
- `--format json-lines` çıktı:
  - Her broken link tek satır: `{"type":"broken_link","from":..,"to":..}`
  - Her orfan not: `{"type":"orphan_note","note":..}`
  - Her orfan tag: `{"type":"orphan_tag","tag":..}`
  - Son satır özet: `{"type":"summary","notes_total":..,"links_total":..,
    "tags_total":..,"broken_links":N,"orphan_notes":N,"orphan_tags":N,
    "clean":bool}`
- `--strict` (SPEC 042) `--format json-lines` ile birlikte çalışır
  (bulgu varsa exit 4 aynı).
- `--dump-report` PATH etkilenmez (SPEC 052 markdown yan etkisi
  format'tan bağımsız).

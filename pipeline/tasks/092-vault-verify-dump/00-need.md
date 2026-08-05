# Görev 092 — İhtiyaç

SPEC 087 `--format json-lines` stdout streaming basar. Büyük vault'ta
kullanıcı `atlas vault verify --format json-lines > report.jsonl` ile
manuel dosyaya redirect ediyor. Doğal `--out PATH` bayrağı yok +
Windows'ta shell redirection karakter kodlaması sorunlarına yol açar.

## Kabul

- `atlas vault verify --format json-lines --out PATH`.
- `--out PATH` **yalnız** `--format json-lines` ile anlamlı.
  Aksi (format=json/json-pretty/human veya format yok) → SPEC HATASI
  exit 2.
- PATH dizini yoksa `parent.mkdir(parents=True, exist_ok=True)`.
- Yazma başarısız (izin/disk) → SPEC HATASI exit 2 (net mesaj).
- `--out` verildiğinde stdout NDJSON basmaz (yalnız dosya).
- Dosya içeriği stdout modu ile BİT-UYUMLU (aynı satırlar + summary).
- `--strict` ve `--dump-report` (SPEC 052 markdown YAN ETKİ) `--out`
  ile ORTOGONAL — biri NDJSON hedef, diğeri markdown yan etki.
- `--out` VERİLMEZSE SPEC 087 BİT-UYUMLU (stdout stream).

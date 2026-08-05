# Görev 092 — Teslim

`atlas vault verify --format json-lines --out PATH`.

## Uygulama

- `_cmd_vault_verify`: `--out` + `fmt != "json-lines"` → SPEC HATASI
  exit 2 (ön-kontrol).
- json-lines dalında `_emit(obj)` lokal helper — `out_fh` var ise
  dosyaya, yoksa `print` (stdout).
- Parent dir auto-mkdir; open("w") başarısız → SPEC HATASI exit 2.
- `try/finally` ile `out_fh.close()` (kaynak sızıntısı yok).
- Parser: `--out PATH` metavar, default None.

## Kanıt

- +10 test (`tests/test_cli_vault_verify_jsonl_out.py`):
  - --out → dosya yazılır, stdout NDJSON basmaz.
  - Dosya içeriği stdout modu ile BİT-UYUMLU (satır bazlı eşitlik).
  - Parent dir auto-mkdir (deep/nested/dir).
  - --out + --format json → exit 2 SPEC HATASI (json-lines mesaj).
  - --out + --format human → exit 2.
  - --out tek başına (format yok) → exit 2.
  - --out + --strict ORTOGONAL (bulgu → dosya YAZILIR + exit 4).
  - --out + --dump-report ORTOGONAL (NDJSON + markdown).
  - Yazma hatası (dosya adı = dizin) → exit 2.
  - --out yoksa SPEC 087 stdout BİT-UYUMLU.
- 1274 → **1284 yeşil** (+10), 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 087: `--out` yoksa stdout stream AYNI.
- SPEC 042: `--strict` exit 4 ve `--dump-report` markdown YAN ETKİ
  format'tan ve `--out`'tan bağımsız.

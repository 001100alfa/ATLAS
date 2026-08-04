# Görev 058 — Teslim

`atlas vault fix-broken` — kırık wikilink'ler için stub not.

## Uygulama

- **`atlas_core/memory/vault_verify.py`**:
  - `StubAction` (frozen): `target/path/sources/action`.
  - `_STUB_TEMPLATE`: markdown şablon (başlık + #stub tag + kaynak
    listesi + timestamp).
  - `create_stub_notes(vault, broken_links, target_dir, *, dry_run)`:
    aynı hedefe birden çok kaynak → TEK stub + kaynaklar sorted/tekil.
    Hedef vault'ta zaten var → `action="skipped"`. Dry-run klasör
    oluşturmaz; apply `mkdir -p parents`.
- **`atlas_core/cli.py::_cmd_vault_fix_broken`**: yeni komut + parser
  alt-komutu (`vault fix-broken`).
- İnsan çıktısı ASCII marker (`.. OK --`) — Windows cp1254 uyumu.

## Kanıtlar

- +14 test (`tests/test_cli_vault_fix_broken.py`):
  - **Birim (7)**: dry-run dokunmaz / apply yazar + template kontrol /
    aynı hedef birden fazla from → tek stub / deterministik sıra +
    kaynak tekilleme / hedef zaten var → skipped / boş broken_links
    → boş liste / StubAction frozen.
  - **CLI (7)**: kırık yok → mesaj / dry-run / apply + audit / custom
    target / vault yok exit 2 / verify bit-uyumlu / apply ikinci kez
    → skipped (stub yeni notu ekledi, kırık link kalmadı).
- Mevcut 39+ vault_verify testi (SPEC 042 + 046 + 052) BİT-UYUMLU.
- 959 → **973 yeşil**, 12 skip, cov %91.23 → %91.32.
- `uv run mypy src` temiz (31 kaynak).
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Yeni alt-komut: `atlas vault fix-broken [--apply] [--target DIR]`.
- Yeni audit action: `fix-broken`.
- Yeni dataclass: `StubAction`.

## Değişmeyen sözleşme

- `atlas vault verify` (SPEC 042) BİT-UYUMLU.
- `atlas vault fix-orphans` (SPEC 046) BİT-UYUMLU.
- `atlas vault verify --dump-report` (SPEC 052) BİT-UYUMLU.
- Exit kodları: 0/2 sınıfı (yeni exit yok).

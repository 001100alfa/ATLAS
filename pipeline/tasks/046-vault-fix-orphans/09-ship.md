# Görev 046 — Teslim

`atlas vault fix-orphans` — orfan notları arşivleyen yıkıcı alt-komut.

## Uygulama

- **`atlas_core/memory/vault_verify.py`**:
  - `OrphanAction` (frozen dataclass): `src, dst, action` (`planned` /
    `moved` / `skipped`).
  - `_find_orphan_paths(vault, names)`: alt-klasördeki notları da bul
    (`rglob("<name>.md")`).
  - `_unique_dst(base)`: çakışma çözümü `<stem>-N.md`; 1000 deneme
    koruması.
  - `archive_orphan_notes(vault, names, target_dir, *, dry_run)`:
    - dry_run → dokunmaz, planlar
    - not dry_run → `target_dir.mkdir(parents=True)` + `shutil.move`
    - kaynak yok → skipped
- **`atlas_core/cli.py::_cmd_vault_fix_orphans`**: yeni komut + parser
  alt-komutu (`vault fix-orphans`). Bayraklar: `--vault-root`,
  `--apply`, `--target`.
- İnsan çıktısı: dry-run/apply etiketi + her not için `src → dst`
  satırı (⋯/✔/⚠ marker).

## Kanıtlar

- +16 test (`tests/test_cli_vault_fix_orphans.py`):
  - Birim (10): `_unique_dst` (3), `_find_orphan_paths` alt-klasör (1),
    `archive_orphan_notes` (dry-run/apply/çakışma/skipped/orfan yok/
    çoklu orfan)
  - CLI (6): dry-run orfan yok / dry-run orfan var / apply taşıma +
    audit / apply custom target / vault yok exit 2 / verify bit-uyumlu
- Mevcut 23 vault_verify testi (SPEC 042 + 052) BİT-UYUMLU.
- 870 → **886 yeşil**, 12 skip, cov %91.10 → %91.21.
- `uv run mypy src` temiz.
- `uv run ruff check src tests` temiz.
- `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Yeni alt-komut: `atlas vault fix-orphans [--apply] [--target DIR]`.
- Yeni audit action: `fix-orphans`.

## Değişmeyen sözleşme

- `atlas vault verify` (SPEC 042) BİT-UYUMLU.
- `atlas vault verify --dump-report` (SPEC 052) BİT-UYUMLU.
- `atlas vault backup/restore` (SPEC 041/041.1) BİT-UYUMLU.
- Exit kodları: 0 (başarı/dry-run), 2 (vault yok) — mevcut sınıf.

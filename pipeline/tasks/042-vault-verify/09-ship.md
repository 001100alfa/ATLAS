# Görev 042 — Teslim

`atlas vault verify` — Obsidian vault graf sağlığı doğrulaması.

## Uygulama

- **Yeni modül**: `atlas_core/memory/vault_verify.py`
  - `BrokenLink` (frozen dataclass): `frm, to` alanları (`from` Python
    rezerve olduğu için `frm`; JSON dışa aktarımda `"from"` yazılır).
  - `VerifyReport` (dataclass): `broken_links, orphan_notes,
    orphan_tags, notes_total, links_total, tags_total`. `is_clean`
    property; `to_dict()` JSON serileştirme.
  - `verify_graph(graph: Graph) -> VerifyReport`: salt-okunur analiz;
    sıralama deterministik.
- `atlas_core/cli.py::_cmd_vault_verify` + parser `verify` alt-komutu
  (`--vault-root`, `--json`, `--pretty`, `--strict`).

## Kanıtlar

- Birim (7): temiz vault / kırık link / orfan not / orfan tag /
  broken_link sıralama / to_dict serileştirme / boş vault.
- CLI (7): insan çıktısı / JSON çıktı / --pretty indent / --strict +
  bulgu exit 4 / --strict + temiz exit 0 / vault yok exit 2 / audit
  kaydı.
- **+14 test** → 783 → **797 yeşil, 12 skip, cov %90.83**.
- `uv run mypy src` temiz; `uv run ruff check src tests` temiz;
  `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Yeni CLI: `atlas vault verify [--json] [--pretty] [--strict]`.
- Yeni exit kodu: **4** (`vault verify --strict` + bulgu).
- Yeni audit action: `verify`.

## Değişmeyen sözleşme

- `Vault` API dokunulmadı (`graph()`, `write`, `daily`, ...).
- `atlas vault backup` / `restore` / `backup --auto|--keep` (SPEC 041,
  041.1) bit-uyumlu.
- Vault üzerinde YAZMA yok (yalnız `_audit_path` yazımı — mevcut
  davranış).

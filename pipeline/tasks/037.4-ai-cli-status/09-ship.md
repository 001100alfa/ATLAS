# Görev 037.4 — Teslim

`atlas ai-cli status <name>` — exec'siz paket sağlık raporu.

## Uygulama

- `atlas_core/cli.py`:
  - `_dir_size_bytes(root)`: rglob toplam byte; symlink izlenmez;
    OSError skip.
  - `_human_bytes(n)`: B / KB / MB / GB eşikleri.
  - `_cmd_ai_cli_status`: rapor dict'i + JSON/insan çıktı çatalı; hata
    yolları (SPEC HATASI + öneri).
  - Parser: `ai-cli status <name> [--json]` alt-komutu.
- Mevcut `_read_installed_version` + `_resolve_ai_cli_bin` (037.2/037.3)
  yeniden kullanıldı — yeni yardımcı eklenmedi.

## Kanıtlar

- +7 test (tests/test_cli_ai_cli_status.py):
  - JSON şema (kurulu + up_to_date=True + boyut + bin)
  - insan çıktısı (satırlar mevcut)
  - up_to_date=False (installed != declared_clean)
  - dependencies'te yok → exit 2
  - kurulu değil → exit 2 + `atlas ai-cli update` önerisi
  - `tools/ai-cli/` yok → exit 2
  - `_human_bytes` sınır değerleri (0, 1023, 1024, 1MB, 1GB)
- 797 → **804 yeşil, 12 skip, cov %90.85**.
- `uv run mypy src` temiz; `uv run ruff check src tests` temiz;
  `uv run atlas scan src` sır bulamadı.

## Yeni davranış

- Yeni CLI: `atlas ai-cli status <name> [--json]`.

## Değişmeyen sözleşme

- SPEC 037 (diff-summary), 037.1 (update), 037.2 (list), 037.3 (exec)
  bit-uyumlu.
- Exit kodları: 037.3 sınıfı (2 = SPEC HATASI; ayrıca 0 = başarı).

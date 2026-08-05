# Görev 060 — Teslim

`atlas ai-cli install <name>` — yeni paket ekleme.

## Uygulama

- `_run_npm_install(bin, package)`: `npm install <package> --save`;
  `cwd = tools/ai-cli`.
- `_cmd_ai_cli_install`: 4-yollu hata (ai-cli dir yok / package.json bozuk /
  npm yok / subprocess çöktü) — hepsi exit 2. npm exit yansıtıldığında
  ≠0 (yükleme başarısız). Başarıda kullanıcıya doğrulama komutları.
- Parser: `install <name>` alt-komutu (positional zorunlu).

## Kanıt

- +7 test (`tests/test_cli_ai_cli_install.py`):
  - `_run_npm_install` argv (subprocess mock)
  - ai-cli dir yok → exit 2
  - npm yok → exit 2
  - başarı → npm çağrılır + doğrulama ipucu
  - npm hata (rc=1) → CLI exit 1
  - subprocess hatası (-1) → exit 2
  - Diğer ai-cli komutları (list --json) bit-uyumlu.
- 1018 → **1025 yeşil**, 12 skip.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 037/037.1/037.2/037.3/037.4/050 hepsi BİT-UYUMLU.

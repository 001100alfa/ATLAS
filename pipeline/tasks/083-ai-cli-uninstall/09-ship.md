# Görev 083 — Teslim

`atlas ai-cli uninstall <name>` — paket kaldırma.

## Uygulama

- `_run_npm_uninstall(bin, package)`: `npm uninstall <name> --save`;
  `cwd=tools/ai-cli`; timeout 600s.
- `_cmd_ai_cli_uninstall`: 4-yollu hata (dir/deps/npm/subprocess) →
  exit 2. npm exit yansır. Başarıda `atlas ai-cli list` ipucu.
- Parser: `uninstall <name>` alt-komutu.

## Kanıt

- +7 test: argv doğru, dir yok, deps'te yok, npm yok, başarı, npm
  hata (exit 1), subprocess hata (exit 2).
- 1179 → **1186 yeşil**.
- mypy/ruff/scan temiz.

## Değişmezlik

- SPEC 037 ailesi BİT-UYUMLU.

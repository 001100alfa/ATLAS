# Görev 037.1 — Teslim

`atlas ai-cli update [--dry-run]` alt-komutu eklendi. Portable
`tools/node/npm.cmd` (win) veya `tools/node/npm` (unix) öncelikli;
yoksa `shutil.which("npm")`. `cwd = tools/ai-cli` sabit.

## Kanıtlar
- `_find_npm_bin` unit: portable → `("path", "portable")`, yoksa → `(None, "")`
- CLI: `tools/ai-cli/` yok → exit 2 + SPEC HATASI
- CLI: npm yok → exit 2 + `npm bulunamadı`
- CLI: `--dry-run` + npm outdated exit 1 → CLI exit 0 (bulgu = hata değil)
- CLI: update npm exit 0 → CLI exit 0
- CLI: subprocess hatası (-1) → exit 2
- +7 test (700 yeşil, cov %90.69)

## Değişmeyen sözleşme
- `ai-cli diff-summary` bit-uyumlu.
- Diğer CLI komutları dokunulmadı.

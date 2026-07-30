# Görev 037.3 — Teslim

`atlas ai-cli exec <name> [args...]` portable launcher.

## Kanıtlar
- Canlı: `atlas ai-cli exec cline --version` → `3.0.47` exit 0
- `_resolve_ai_cli_bin`: Windows `.cmd` öncelik; Unix çıplak isim
- Bin yok → exit 2 + `atlas ai-cli list` önerisi
- `tools/ai-cli/` yok → exit 2 + SPEC HATASI
- Sahte bin exit 7 → CLI exit 7 (yansıtma)
- +5 test (747 yeşil, cov %90.56)

## Değişmeyen sözleşme
- `ai-cli diff-summary` (037), `update` (037.1), `list` (037.2) bit-uyumlu.

# Görev 037.2 — Teslim

`atlas ai-cli list [--json]` alt-komutu eklendi. `package.json`
dependencies + `node_modules/<n>/package.json` version cross-check.

## Kanıtlar
- Canlı: 3 paket görünür (@kilocode/cli 7.4.16, cline 3.0.47,
  opencode-ai 1.18.9)
- Boş deps → "(paket yok)"
- Kurulu değil → "(kurulu değil)" insan / `null` JSON
- JSON şeması: `{"path": "...", "packages": [{"name","expected","installed"}]}`
- Bozuk package.json → exit 2 + SPEC HATASI
- +5 test (727 yeşil, cov ≥ %90)

## Değişmeyen sözleşme
- `ai-cli diff-summary` (037), `ai-cli update` (037.1) bit-uyumlu.

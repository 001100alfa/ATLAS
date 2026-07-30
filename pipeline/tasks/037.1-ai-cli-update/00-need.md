# Görev 037.1 — İhtiyaç

`atlas ai-cli diff-summary` (037) commit disiplinini kurdu, ama
gerçekten güncellemeyi kullanıcı manuel yapıyor:

```
cd tools\ai-cli
..\node\npm.cmd update
```

Tek komut wrap: `atlas ai-cli update [--dry-run]`.

## Kabul kriteri
- `atlas ai-cli update` → `tools/ai-cli/` içinde `npm update` çalıştırır.
- Portable öncelik: `tools/node/npm.cmd` (win) / `tools/node/npm` (unix)
  → sistem `npm` (PATH).
- `--dry-run` → `npm outdated --long` (yıkıcı işlem yok); npm'in 1
  (bulgu var) exit'i dry-run modunda 0 olarak yansıtılır.
- Uygula → npm exit kodu doğrudan yansıtılır (0/1).
- npm bulunamadı → stderr `SPEC HATASI: npm bulunamadı…` + exit 2.
- `tools/ai-cli/` yoksa → exit 2.

## Riskli
- Subprocess timeout (600s) — npm update büyük ağaçlarda yavaş
  olabilir; test yok, canlı çalıştırıldığında görülecek.
- npm stderr'inde "notice" mesajlarını normal görsün.

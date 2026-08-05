# Görev 083 — İhtiyaç

SPEC 060 `install` var; ama kullanıcı bir paketi kaldırmak isterse
manuel `cd tools/ai-cli && ../node/npm.cmd uninstall <pkg>`. Tamamlayıcı
`atlas ai-cli uninstall` doğal.

## Kabul

- `atlas ai-cli uninstall <name>`.
- `npm uninstall <name> --save` (deps.json güncelle).
- Package deps'te olmalı; yoksa exit 2 + `atlas ai-cli list` önerisi.
- Exit: 0 başarı; npm exit yansır; 2 dir/deps/npm/subprocess hataları.
- İpucu: kaldırma sonrası `atlas ai-cli list`.

## Değişmezlik

- SPEC 037/037.1/037.2/037.3/037.4/050/060 hepsi BİT-UYUMLU.

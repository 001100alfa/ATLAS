# Görev 060 — İhtiyaç

SPEC 037.1 `update` mevcut paketleri günceller; 050 tek paket güncellemesi.
Ama yeni paket eklemek için hâlâ `cd tools/ai-cli && ../node/npm install <pkg>`
gerek. Bir kullanıcı `codex-cli`, `gemini-cli` gibi yeni bir CLI denemek
isterse süreç ağır.

## Kabul

- `atlas ai-cli install <name>` — `npm install <name> --save` wrap.
- Portable npm önce (`tools/node/`); sistem PATH fallback.
- Exit: 0 başarı; npm exit ≠0 yansıtılır; 2 `tools/ai-cli/` yok /
  npm yok / subprocess çöktü.
- İpucu: kurulum sonrası `atlas ai-cli status <name>` + `list` öner.

## Risk

- npm sürüm sabitleme: `--save` yeterli (npm 7+ default; explicit).
  Belirli sürüm için kullanıcı `install <pkg>@1.2.3` yazabilir (npm
  argv aynen forward).
- Aynı paket zaten kurulu ise `npm install` idempotent — dokunmaz veya
  yeni sürüm çeker (npm politikasına bırakıldı).

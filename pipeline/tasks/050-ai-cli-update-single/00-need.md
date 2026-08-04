# Görev 050 — İhtiyaç

`atlas ai-cli update` şu an tüm paketleri güncelliyor. Ama operasyonda:
- Yeni bir opencode-ai sürümü çıktı, cline'ı olduğu yerde tutmak istiyoruz
- CI'de sadece belirli paketi test etmek istiyoruz

Şu an tek yol: `cd tools/ai-cli && ../node/npm.cmd update opencode-ai` —
portable npm yolunu manuel bulmak ve `cd` yapmak gerek.

## Kabul kriteri

- `atlas ai-cli update <name>` — sadece o paketi günceller.
- `atlas ai-cli update <name> --dry-run` — sadece o paketin outdated'ini
  gösterir.
- `atlas ai-cli update` (name yok) — mevcut davranış BİT-UYUMLU
  (hepsini günceller).
- `<name>` `package.json` dependencies'te olmalı; aksi hâlde
  exit 2 SPEC HATASI + `atlas ai-cli list` önerisi.
- Konsol çıktısı: `[ai-cli] npm update (opencode-ai) (portable: ...)`
  — paket adı parantezi source label'dan önce.
- Argv: `npm update <name>` / `npm outdated --long <name>`.

## Riskli

- Mevcut `_run_npm_update(bin, dry_run)` imzası (`package: str | None
  = None`) opsiyonel keyword arg olarak genişletildi. Mock lambdaları
  (`lambda _b, _d: ...`) TypeError verirdi → 3 mevcut test güncellendi:
  `lambda _b, _d, package=None: ...`. Semantik değişmedi.
- SPEC 037.1 exit sözleşmesi korunur: dry-run npm exit yansıtılmaz;
  update npm exit doğrudan yansır.

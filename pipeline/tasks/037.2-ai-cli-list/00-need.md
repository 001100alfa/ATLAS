# Görev 037.2 — İhtiyaç

`atlas ai-cli update` (037.1) paketleri güncelliyor ama kullanıcı
hangi paketlerin kurulu olduğunu, beklenen vs kurulu sürümü tek yerde
göremiyor. Manuel: `cat tools/ai-cli/package.json` + her paket için
`cat node_modules/<n>/package.json | grep version`.

Tek komut: `atlas ai-cli list [--json]`.

## Kabul kriteri
- `package.json` dependencies alanı kaynak; her paket için
  `node_modules/<n>/package.json` version yüklenir.
- `installed=null` → paket kurulu değil (`(kurulu değil)` insan
  formatı; JSON `null`).
- `--json` yapılandırılmış çıktı: `{"path": ..., "packages": [...]}`.
- İnsan format hizalı sütunlar (name / expected / installed).
- `tools/ai-cli/` yoksa exit 2 + SPEC HATASI.
- `package.json` yoksa/bozuksa exit 2.

## Riskli
Yok — pure read + format.

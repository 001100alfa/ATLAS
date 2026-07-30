# Görev 037.3 — İhtiyaç

037.2 (`list`) kurulu paketleri listeliyor; 037.1 (`update`)
güncelliyor. Ama kullanıcı `opencode` veya `cline`'ı çağırmak için
manuel path yazıyor: `tools\ai-cli\node_modules\.bin\opencode.cmd`.

Tek komut: `atlas ai-cli exec <name> [args...]`.

## Kabul kriteri
- `tools/ai-cli/node_modules/.bin/<name>` — Windows: `.cmd` öncelik;
  Unix: çıplak isim + executable bit.
- Kullanıcı arg'ları subprocess'a aynen forward; exit kodu doğrudan
  yansır.
- Bin bulunamadı → exit 2 + öneri (`atlas ai-cli list`).
- `tools/ai-cli/` yok → exit 2 + SPEC HATASI.

## Riskli
- `argparse.REMAINDER` — deprecate niyetinde ama şu an tek yol; `--`
  ayrıcalıklarını (flag'leri forward) korur.
- Windows `.cmd` shim çalıştırma: `subprocess.run([...])` argv liste
  ile — Python `.cmd` uzantısını tanıyıp cmd.exe altında çalıştırır.

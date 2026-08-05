# Görev 085 — İhtiyaç

SPEC 079 `--sort-by` ile sıralanmış tam liste geliyor. "En büyük 5
arşiv" ya da "son 3 tarih" için `head`/`tail` gerek. Doğal top-N
bayrağı yok.

## Kabul

- `atlas archive --list --sort-by KEY [--desc] --limit N`.
- `N > 0` int; `N=0` veya negatif → argparse SystemExit(2) veya
  SPEC HATASI exit 2 (int çevrimi + doğrulama).
- `--limit` VERİLMEZSE davranış SPEC 079/075 BİT-UYUMLU (tam liste).
- `--limit` sıralamadan SONRA uygulanır (top-N, orta-N değil).
- Hem `--json` hem pretty çıktı `--limit` uyar.
- `N > len(entries)` → tüm liste (kesme yok, hata değil).

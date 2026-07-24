# 03 — Paket Yürütme  `/execute-wp`

**Amaç:** WP'leri sırayla kapatmak, her biri commit'le.

| | |
|---|---|
| **Girdi** | Sıralı WP listesi |
| **Çıktı** | WP başına >= 1 commit + log satırı |

## Prosedür
1. WP başla -> kodla -> WP doğrulaması yeşil -> commit.
2. Commit mesajı: 'WP-N: <özet>' + gövdede karar notu.
3. 3 denemede geçmeyen doğrulama -> DUR, sorunu raporla.

## Kapıya Katkısı
Gate: 'tüm WP'ler commit'e bağlı' sağlanır.

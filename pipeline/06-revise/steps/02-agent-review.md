# 02 — Bağımsız İnceleme  `/agent-review`

**Amaç:** reviewer subagent'ı taze bağlamla koşturmak.

| | |
|---|---|
| **Girdi** | Temizlenmiş diff |
| **Çıktı** | Ham bulgu listesi |

## Prosedür
1. Subagent'a SADECE diff + spec ver — build sohbet geçmişini VERME.
2. Talimat: güvenlik -> birim/mantık -> kenar -> performans sırası.
3. Bulgular dosya:satır formatında toplanır.

## Kapıya Katkısı
Yazar körlüğü kırılır.

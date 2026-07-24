# 03 — Hata Sözleşmesi  `/error-contract`

**Amaç:** Doğru exception + doğru mesaj garantisi.

| | |
|---|---|
| **Girdi** | Spec hata tanımları |
| **Çıktı** | pytest.raises testleri (mesaj eşleşmeli) |

## Prosedür
1. Her hata koşulu: beklenen exception tipi VE mesaj içeriği.
2. Genel Exception yakalama testte de kodda da yasak.
3. Hata mesajı kullanıcıya girdisini geri söylemeli (debug kolaylığı).

## Kapıya Katkısı
Hatalar da davranıştır — sözleşmeye bağlanır.

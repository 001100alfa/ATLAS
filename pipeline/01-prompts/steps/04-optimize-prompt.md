# 04 — Optimizer  `/optimize-prompt`

**Amaç:** Yönergeyi model için sıkılaştırmak: sıra, vurgu, format.

| | |
|---|---|
| **Girdi** | Taslak + bilgi haritası |
| **Çıktı** | Optimize edilmiş yönerge gövdesi |

## Prosedür
1. Kritik kısıtları başa ve sona koy (primacy/recency).
2. Uzun paragrafları maddelere kır; her madde tek talimat.
3. Çıktı formatını ŞEMA olarak ver (dosya adı, imza, birim).

## Kapıya Katkısı
Yönerge modelin yanlış yorumlayamayacağı forma gelir.

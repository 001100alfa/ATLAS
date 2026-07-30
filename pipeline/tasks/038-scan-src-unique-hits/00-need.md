# Görev 038 — İhtiyaç

`atlas doctor --scan-src` çıktısı `total` (ham bulgu) verir; ama bir
dosyada birden çok kalıp yakalanınca kullanıcı **kaç tekil dosyayı
düzeltmesi gerektiğini** göremez. `sample_files` ilk 5 unique yolu
gösterir ama toplam tekil dosya sayısı yok.

## Kabul kriteri
- `quality.scan_src` şemasına `unique_hits: int` eklenir.
- Yol yoksa `unique_hits = 0` (ile beraber `warning: "scan hedefi yok…"`).
- İnsan format satırında `(N bulgu, M tekil dosya)` görünür.
- `sample_files`, `total`, `warning` alanları AYNI.
- Şema versiyonu değişmez (yalnız alan eklendi).

## Riskli
Yok — pure additive.

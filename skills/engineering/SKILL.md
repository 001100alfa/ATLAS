# Mühendislik Hesap Kuralları

## Birimler
- İç hesap SI-mm sistemi: mm, N, MPa (N/mm²), Nmm.
- Girdi/çıktı dönüşümleri fonksiyon sınırında yapılır,
  hesap çekirdeğine karışık birim girmez.

## Kesit hesabı
- Değişken adları EN 1993 gösterimi: A, Iy, Iz, Wel_y, Wpl_y.
- Kaynaklı I-kesit: gövde + 2 flanş ayrıştır, paralel eksen
  teoremi ile Iy topla; doğrulama HEB/IPE katalog değeriyle.

## EN 12663 (demiryolu araç gövdesi)
- Yük durumları kategoriye göre (F-I, F-II, P...); emniyet
  katsayıları ve kombinasyonlar standarttan alınır, ezbere değil.
- S355: fy=355 MPa (t≤16mm), t arttıkça fy düşer — tablo kontrol.

## Çizim çıktısı
- DXF: ezdxf, R2010 formatı; katman adları TR-büyük harf.
- SVG: 1 birim = 1 mm, viewBox gerçek boyut; ölçü okları dahil.

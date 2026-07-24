# NEED-001: Kesit özellik hesaplayıcı
**Tarih:** 2026-04-16 | **Talep eden:** ARTEMIS | **Öncelik:** P0
## Problem
Wagon kiriş boyutlandırmasında kesit özellikleri her seferinde elle
hesaplanıyor; yavaş ve hataya açık.
## Başarı Ölçütü
I ve kutu kesit için A, Iy, Iz, Wel, Wpl, kg/m; el hesabı referanslarıyla
rel_tol=1e-9 içinde; CLI'dan <1 sn'de sonuç.
## Kapsam DIŞI
- Fillet/radius'lu hadde profiller (v0.2'ye)
- Burulma sabiti It, çarpılma Iw
## Kısıtlar
SI-mm, EN 1993 gösterimi, Python 3.12, mypy strict.

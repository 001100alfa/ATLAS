# Görev 038 — Teslim

`quality.scan_src` şemasına `unique_hits: int` eklendi. `_check_scan_src`
zaten `seen: set[str]` tutuyordu (sample_files unique için) — artık
`len(seen)` değeri de sözleşmenin parçası. İnsan formatı `(N bulgu,
M tekil dosya)` satırı üretir. Şema v1 korundu (alan eklendi, kaldırma
yok).

## Kanıtlar
- `_check_scan_src` unit: total=3, unique_hits=2 (2 dosyada 3 bulgu)
- CLI JSON: `data["quality"]["scan_src"]["unique_hits"] == 1`
- İnsan format: `"1 bulgu, 1 tekil dosya"` satırı
- Yol yok: `unique_hits == 0` + `warning`
- 697 test yeşil (baseline 693 + 4), cov %91.11

## Kırılan sözleşme
Yok. Mevcut testler substring kontrolü yaptığı için `"0 bulgu"` hala
geçer.

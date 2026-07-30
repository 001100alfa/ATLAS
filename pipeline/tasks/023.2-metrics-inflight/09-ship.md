# Görev 023.2 — Teslim

`atlas metrics` insan çıktısına inflight ortalama/pik satırı.

## Kanıtlar
- 3 kayıt (inflight 1,2,3) → `inflight avg/max: 2.00 / 3 (3 kayıtta)`
- Karma (inflight'lı + inflight'sız) → sadece inflight'lı sayılır
- Hiç inflight yok → satır BASILMAZ (bit-uyumluluk)
- `--json` bit-uyumlu (ham kayıtlar)
- +4 test (746 yeşil, cov %90.68)

## Değişmeyen sözleşme
- Mevcut SPEC 023/029 testleri (13 test) bit-uyumlu.
- `--json` çıktı formatı aynı (ham liste).

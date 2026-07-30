# Görev 023.2 — İhtiyaç

SPEC 039 metrics kayıtlarına `inflight: int` opt-in alan ekledi. Ama
`atlas metrics` bunu görmezden geliyor — kullanıcı ortalama/pik
eş-zamanlı çağrı sayısını görmüyor.

## Kabul kriteri
- `atlas metrics` insan çıktısına `inflight avg/max: A.AA / N (K
  kayıtta)` satırı EKLENİR.
- `inflight` alanı olmayan kayıtlar skip (bit-uyumluluk — eski kayıtlar
  veya SPEC 039 öncesi run'lar).
- Hiç `inflight` yoksa satır BASILMAZ (gürültü yok).
- `--json` çıktısı bit-uyumlu — ham kayıtları döner (inflight alanı
  varsa görünür, yoksa yok).

## Riskli
Yok — pure agregasyon.

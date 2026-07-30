# 032.2 — İhtiyaç: `atlas doctor --scan-src` birleştirme

## Bağlam
034 pre-commit hook shim'i şu an iki komut çağırıyor:
```sh
atlas scan src && atlas doctor --strict
```
İkisi de exit koduyla ayrı sinyal veriyor, hook `&&` ile zincirliyor.
Bu iyi ama iki subprocess başlatıyor + iki farklı komut sözleşmesi
akışta. `atlas doctor` "kalite gate" olarak konumlandığı için,
sır taraması da aynı çatı altında hizmet vermek doğal.

032.1 üç kanalı `_has_quality_warning` yolu ile birleştirdi;
`--scan-src` dördüncü kanal olur — tek subprocess, tek exit noktası,
kalite gate'in tam ifadesi.

## İhtiyaç (tek cümle)
`atlas doctor --scan-src` opt-in bayrağı verildiğinde, `scan_secrets`
kaynak dizinine uygulansın; bulgu varsa `quality.scan_src.warning`
dolar; `--strict` altında exit 9 (`_has_quality_warning` yolu).

## Ölçülebilir Başarı
- **M1 — CLI:** `atlas doctor --scan-src` bayrağı; varsayılan kapalı
  (ekstra maliyet yok). `--scan-src <path>` opsiyonel — varsayılan
  `src`.
- **M2 — `_check_scan_src(path)` yardımcısı:** dizinde `scan_secrets`
  çalıştırır; bulgu sayısı + dosya-bazlı özet + `warning` (>0 ise).
- **M3 — Rapor entegrasyonu:** `--scan-src` verildiğinde `report[
  "quality"]["scan_src"]` alanı eklenir. Bayrak yoksa alan **eklenmez**
  (bit-uyumluluk: doctor mevcut yavaşlığı korunur).
- **M4 — İnsan format:** bayrak verildiyse `[Kalite kapıları]` altına
  `sır taraması:` satırı eklenir; bulgu varsa `[!]` prefix +
  ilk 5 bulgu dosyası özet.
- **M5 — Strict davranışı:** `_has_quality_warning(report)` zaten
  `quality.*.warning` alanlarına bakıyor — `scan_src.warning` de
  otomatik yakalanır (032.1 tek kanal yolu).
- **M6 — Hook shim güncelleme:** `tools/hooks/pre-commit` tek satır:
  `atlas doctor --strict --scan-src`. İki komut yerine tek. `atlas
  scan src` sözleşmesi (mevcut `_cmd_scan`) DEĞİŞMEZ — kullanıcı
  hâlâ elle çalıştırabilir.
- **M7 — Bit-uyumluluk:** `--scan-src` yoksa doctor mevcut davranış
  (JSON alanları + insan çıktısı korunur). `atlas scan src` komutu
  bağımsız yaşamaya devam.
- **M8 — Test:** +5-6 test.
- **M9 — DECISIONS:** [KARAR] neden `_cmd_scan` silinmedi (bağımsız
  kullanım); neden opt-in (ekstra IO maliyet); hook shim'i sürüm
  atlasın (`# atlas-hook v2`?).

## Kapsam DIŞI
- Custom scan paths (birden fazla dizin) — `--scan-src <path>`
  tekli yeter.
- Custom scan config (regex override) — YAGNI, `scan_secrets`
  sözleşmesi zaten güçlü.
- `atlas scan` komutunun kendisi geliştirmesi — bağımsız iş.

## Kısıt
- `_cmd_doctor`, `_collect_doctor_report` çıktı + JSON alanları
  KORUNUR; yeni `quality.scan_src` yalnız bayrak varsa görünür.
- `_cmd_scan` (mevcut `atlas scan`) sözleşmesi DEĞİŞMEZ.
- `scan_secrets` API'si (`security/`) DEĞİŞMEZ.
- Hook shim'i imza `# atlas-hook v1` → `v2` (034.1 için status'ta
  eski v1 shim'i "eski" işaretlenir, kullanıcı `atlas hooks install`
  ile günceller — mevcut mekanizma).
- Yeni env DEĞİL, yeni exit kodu YOK (9 mevcut).
- Türkçe uyarı.

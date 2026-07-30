# 032 — İhtiyaç: `atlas doctor --strict` quality gate

## Bağlam
DECISIONS.md doktrini var: "önemli karar / öğrenilen hata →
DECISIONS.md'ye ekle" (CLAUDE.md §Zorunlu Döngü). Ancak bu bir
disiplin — kimse denetlemiyor. Aşırı iş yoğunluğunda ya da unutkanlıkta
DECISIONS güncel kalmaz; sonraki oturumlar drift yakalar, tarih
tutmayan kayıtlar boşluk üretir.

Yine coverage/kalite eşikleri `pytest --cov-fail-under=90` ile ayrı
komutlarda kontrol ediliyor — CI'de var, ama commit öncesi lokal
tek komutla "her şey yolunda mı" sorusu yok. `atlas doctor` env
sağlığını gösterir, davranışsal kalite değil.

## İhtiyaç (tek cümle)
`atlas doctor --strict` opt-in bayrağı, DECISIONS.md drift denetimi
yapsın; drift eşik aşımı varsa **exit 9** ile dursun; `--strict`
verilmediğinde mevcut davranış birebir korunsun.

## Ölçülebilir Başarı
- **M1 — DECISIONS drift denetimi:** DECISIONS.md'nin en üstteki
  `^## YYYY-MM-DD` tarihi ile bugün tarihi arasındaki gün farkı
  hesaplanır. `days >= threshold` → uyarı.
- **M2 — Eşik env:** `ATLAS_STRICT_DRIFT_DAYS` (varsayılan 7).
  Parse hatası / 0 / negatif → varsayılan (026.1 fail-safe kalıbı).
- **M3 — Rapor entegrasyonu:** `_collect_doctor_report`'a
  `"quality": {"decisions_drift": {...}}` bölümü. JSON çıktısında
  her zaman görünür (bayraktan bağımsız). İnsan formatında
  `[Kalite kapıları]` bölümü altında.
- **M4 — `--strict` bayrağı:** verildiğinde ve `quality.decisions_drift.
  warning` doluysa **exit 9** döner. Bayrak yoksa mevcut davranış
  (exit 0) korunur.
- **M5 — DECISIONS eksik/parse hata:** dosya yok veya tarih
  bulunamadıysa `warning: "DECISIONS.md yok veya tarih parse
  edilemedi"` + strict exit 9. "Belge yok" da bir sorun.
- **M6 — Yeni exit kodu 9:** "quality gate failed". 8 = `atlas
  metrics --alert` (029); 9 farklı semantik.
- **M7 — Bit-uyumluluk:** `--strict` yoksa `_cmd_doctor` çıktısı
  ve exit kodu birebir korunur (yalnız insan formatına `[Kalite
  kapıları]` bölümü eklenir; JSON'a `"quality"` alanı eklenir —
  eski JSON tüketicileri eski alanları hâlâ görür).
- **M8 — Test:** +6-8 test — drift yok, drift var+strict, drift
  var+strict yok (uyarı görünür exit 0), DECISIONS yok+strict,
  eşik env override, tarih parse hatası, JSON çıktısında alan
  varlığı, yeni exit 9.
- **M9 — DECISIONS:** [KARAR] yeni exit 9 semantiği; neden
  bugün-tarih baz (commit tarihi değil); neden 7 gün eşik.

## Kapsam DIŞI
- Coverage eşiği denetimi (`pytest --cov-fail-under`) — mevcut
  pytest doğal olarak yapıyor; dublikasyon YAGNI.
- Test failure denetimi — pytest zaten kırar; `atlas doctor`
  pytest çalıştırmaz.
- DECISIONS entry count / feat commit count karşılaştırması —
  YAGNI, tarih drift'i yeter.
- Otomatik "DECISIONS'a ekle" — YAGNI, kullanıcı yazar.
- Ruff/mypy denetimi — ayrı komutlar; doctor env sağlık, quality
  değil.
- Pre-commit hook — `atlas doctor --strict` manuel/CI'ye bağlanır;
  hook otomasyonu ayrı iş.

## Kısıt
- `_cmd_doctor` ve `_collect_doctor_report` mevcut sözleşme +
  çıktı korunur; yalnız EKLEMELER.
- Yeni env: `ATLAS_STRICT_DRIFT_DAYS`.
- Yeni exit: **9** ("quality gate failed").
- Türkçe uyarı mesajı.
- Windows/Unix ortak — dosya + tarih; platform-özel dallanma yok.
- DECISIONS.md yolu proje kökünden (`Path("DECISIONS.md")`) —
  test için parametrize edilir.

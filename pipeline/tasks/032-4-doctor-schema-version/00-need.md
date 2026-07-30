# 032.4 — İhtiyaç: `atlas doctor` JSON çıktısına `schema_version` alanı

## Bağlam
`atlas doctor --json` şeması bugüne kadar birkaç iterasyonla büyüdü:
- 021 initial
- 021.1 JSON
- 021.2 `ping` alanı
- 032 `quality.decisions_drift`
- 032.1 `quality.entry_count`, `quality.vault_health`
- 032.2 `quality.scan_src` (opsiyonel)
- 034.1 `quality.*` bağlamında değişmeden — ancak hooks status'da
  `shell_available`, `shell_path` (ayrı komut)

Şu ana kadar **hep EKLEMELER** olmuş (breaking yok). Ancak
ilerideki turlarda alan kaldırma / yeniden isimlendirme olursa CI
tüketicileri (JSON parse edenler) sessizce kırılır. Bir
`schema_version` alanı olsa tüketici "beklenmedik sürüm → uyar/dur"
yapabilir.

## İhtiyaç (tek cümle)
`atlas doctor` çıktısına (hem insan başlık hem JSON en üst) sabit
`schema_version = "1"` alanı eklensin; ilerideki breaking değişiklikte
`"2"`'ye zıplar.

## Ölçülebilir Başarı
- **M1 — JSON alanı:** `_collect_doctor_report`'un döndürdüğü dict'e
  `"schema_version": "1"` en üst alan olarak eklenir. Mevcut alanlar
  aynen — sadece eklenir.
- **M2 — İnsan format:** ilk satır `=== ATLAS doctor — env sağlık
  kontrolü (şema v1) ===` (parantez içinde şema versiyonu).
- **M3 — Sabit:** modül seviyesinde `_DOCTOR_SCHEMA_VERSION = "1"`
  — testler ve gelecek bump'lar tek yerden.
- **M4 — Semver stratejisi:** string sabit (semver değil, integer-
  like). Ekleme (yeni alan) = versiyon aynı. Kaldırma / rename /
  tip değişikliği = major bump (`"2"`, `"3"`...).
- **M5 — Bit-uyumluluk:** mevcut JSON tüketicileri hâlâ eski alanları
  görür; yeni tüketiciler `schema_version` üzerinden karar verebilir.
- **M6 — Test:** +3 test — JSON `schema_version == "1"`; insan
  format başlığında "şema v1" görünür; mevcut alanlar (backend,
  warnings, quality, storage) regresyon.
- **M7 — DECISIONS:** [KARAR] `"1"` string neden semver değil (basit
  bump disiplini); bump kuralları (kaldırma/rename = major; ekleme =
  aynı).

## Kapsam DIŞI
- `atlas metrics --json` şema versiyonu — YAGNI (o çıktı liste,
  şema evrimi doktor'a oranla dar).
- `atlas replay --list --json` şema versiyonu — YAGNI.
- `atlas hooks status --json` şema versiyonu — YAGNI (034 kalıbı).
- Minor bump kuralları (`"1.1"`, `"1.2"`) — YAGNI, string sabit
  yeter.
- Şema kaydı ayrı JSON schema (JSON Schema Draft) — YAGNI, tüketici
  şu an alan varlığıyla kontrol yapar.

## Kısıt
- `_cmd_doctor` çıktı sözleşmesi (hem insan hem JSON) BİREBİR
  korunur; yalnız EKLEMELER (`schema_version` alanı + başlık
  parantezi).
- Yeni env DEĞİL, yeni exit kodu YOK.
- Türkçe başlık.

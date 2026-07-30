# 032.4 — Ship

## Sonuç
- **`schema_version: "1"`** alanı `atlas doctor` çıktısına eklendi:
  - JSON: en üst alan (`{"schema_version": "1", "backend": ...}`)
  - İnsan: başlık `=== ATLAS doctor — env sağlık kontrolü (şema v1) ===`
- **Modül sabiti** `_DOCTOR_SCHEMA_VERSION = "1"` — tek yerden bump.
- **Bump kuralları (DECISIONS):**
  - Alan **ekleme** → versiyon AYNI kalır (bit-uyumlu).
  - Alan **kaldırma / rename / tip değişikliği** → **major bump**
    (`"2"`, `"3"`...).
  - Minor bump ("1.1") YOK — string sabit yeter.
- **Bit-uyumluluk:** mevcut JSON alanları BİREBİR korundu (backend,
  retry_pricing, storage, warnings, quality.decisions_drift/
  entry_count/vault_health/scan_src[opt]). Yeni tüketiciler
  `schema_version` üzerinden karar verebilir; eskiler eski alanları
  görmeye devam eder.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_DOCTOR_SCHEMA_VERSION="1"
                                            modül sabiti;
                                            _collect_doctor_report'a
                                              "schema_version" en üst
                                              alan olarak;
                                            _cmd_doctor insan format
                                              başlığı "(şema v1)")
tests/test_cli_doctor_strict.py           (+4 test 032.4: JSON alanı,
                                            JSON regresyon (mevcut alanlar
                                            korundu), insan format
                                            başlıkta 'şema v1', modül
                                            sabiti)
pipeline/tasks/032-4-doctor-schema-version/*.md (2 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_doctor` mevcut çıktı + JSON alanları BİREBİR (yalnız EKLEMELER:
  `schema_version` alanı + başlık parantezi).
- `_collect_doctor_report` şemasında sadece ek alan.
- Test regresyon: mevcut 45 test aynen geçiyor.

## Kalite kapıları
- pytest: **680 passed + 12 skipped** (676 → +4)
- coverage: %91.17
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/032.4-doctor-schema-version` — 036 üstünde tek commit.

## Env sözleşmesi
Değişmedi. Yeni exit kodu YOK.

## Kullanım örneği (CI kalıbı)
```bash
$ atlas doctor --json --strict > doctor.json
$ jq -r '.schema_version' doctor.json
1

# CI script:
if [ "$(jq -r '.schema_version' doctor.json)" != "1" ]; then
    echo "UYARI: ATLAS doctor şeması değişti — CI parser'ı güncellemesi lazım"
    exit 2
fi
```

## Şema kapsamı (v1'de sabit)
- `schema_version`: "1"
- `backend`: LLM backend + timeout + resolved bin
- `retry_pricing`: retry sayıları, backoff, jitter, cost env
- `storage`: vault, audit, sandbox, context, archive age
- `warnings`: `str[]` env sağlık uyarıları
- `quality`:
  - `decisions_drift` (032)
  - `entry_count` (032.1)
  - `vault_health` (032.1)
  - `scan_src` (032.2, opsiyonel — yalnız `--scan-src` verildiyse)
- `ping` (opsiyonel — yalnız `--ping` verildiyse, 021.2)

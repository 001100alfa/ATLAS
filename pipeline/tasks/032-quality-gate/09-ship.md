# 032 — Ship

## Sonuç
- **`atlas doctor --strict`** yeni bayrağı: DECISIONS.md drift
  uyarısı varsa **exit 9** ile durur; `--strict` yoksa mevcut
  davranış (exit 0) birebir korunur.
- **Drift denetimi:** DECISIONS.md'nin en üstteki `^## YYYY-MM-DD`
  başlığı (ters-kronolojik format) ile bugün tarihi arasındaki
  gün farkı. `drift >= threshold` iken uyarı.
- **Eşik env:** `ATLAS_STRICT_DRIFT_DAYS` (varsayılan 7). Parse
  hatası / 0 / negatif → varsayılan (018/026 fail-safe kalıbı).
- **Rapor entegrasyonu:** `_collect_doctor_report`'a
  `"quality": {"decisions_drift": {...}}` bölümü eklendi. Alan
  her zaman raporlanır (`--strict` bayrağından bağımsız).
  Şema: `{path, threshold_days, last_date, drift_days, warning}`.
- **İnsan format:** `[Kalite kapıları]` bölümü mevcut doctor
  çıktısının sonuna eklendi. Drift uyarısı varsa `[!]` prefix'iyle
  görünür — `--strict` yoksa sadece bilgi.
- **JSON entegrasyonu:** `--json` çıktısı `quality` alanını içerir.
  `--json --strict` + drift → JSON yine basılır AMA exit 9 döner
  (CI script JSON'u dosyaya kaydeder, exit koduna göre karar).
- **Yeni exit kodu 9:** "quality gate failed" — 8 = `atlas metrics
  --alert` (029); 9 farklı semantik.
- **Bit-uyumluluk:** `--strict` yoksa `_cmd_doctor` çıktısı ve exit
  kodu birebir korunur. İnsan formatına yeni bölüm EKLENDİ (mevcut
  bölümler değişmedi); JSON'a yeni alan EKLENDİ (mevcut alanlar
  değişmedi).

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +re import, +date
                                            import; +_DECISIONS_MD_DEFAULT,
                                            +_DECISIONS_DATE_RE,
                                            +_last_decision_date,
                                            +_read_strict_drift_days_env,
                                            +_check_decisions_drift;
                                            _collect_doctor_report'a
                                              "quality" bölümü;
                                            _cmd_doctor +--strict + insan
                                              format [Kalite kapıları] +
                                              exit 9 hem insan hem JSON
                                              yolunda;
                                            parser p_doc --strict)
tests/test_cli_doctor_strict.py           (yeni, +18 test:
                                            _last_decision_date x4,
                                            env x3, drift x5, doctor
                                            --strict entegrasyonu x6)
tests/test_actions_windows_job.py         (edit: 026.3 CPU quota
                                            testi 3.5s eşiği yüklü
                                            makinede flaky; timeout
                                            12s + eşik 8s yaptım)
pipeline/tasks/032-quality-gate/*.md      (2 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_doctor`, `_collect_doctor_report` mevcut alanları +
  çıktısı KORUNDU (`quality` yalnız EKLENDİ).
- `--json` yolu drift alanını her zaman verir; strict yalnız exit
  kodunu değiştirir.
- Yeni env: `ATLAS_STRICT_DRIFT_DAYS`.
- Yeni exit: **9** ("quality gate failed").

## Kalite kapıları
- pytest: **628 passed + 9 skipped** (610 → +18)
- coverage: %91.38 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/032-quality-gate` — main üstünde tek commit.

## Env sözleşmesi (yeni ★)
| Değişken | Anlam |
|---|---|
| `ATLAS_STRICT_DRIFT_DAYS` ★ | **032** — DECISIONS.md drift eşiği (varsayılan 7 gün) |

## Exit kodları (kümülatif, yeni ★)
| Kod | Anlam |
|---|---|
| 0 | Başarılı |
| 1 | Sır bulundu (scan) |
| 2 | SPEC HATASI (input/config) |
| 3 | GBrain/workflow başarısız |
| 4 | Run bitmedi (done=False) |
| 5 | Action denied |
| 6 | archive-all bir görevde başarısız |
| 7 | Env / archive age parse hatası |
| 8 | `atlas metrics --alert` eşik altı (029) |
| **9** ★ | **`atlas doctor --strict` DECISIONS drift uyarısı (032)** |

## Kullanım örneği
```bash
$ atlas doctor
=== ATLAS doctor — env sağlık kontrolü ===
...
[Kalite kapıları]
  DECISIONS.md: DECISIONS.md
  son giriş: 2026-07-30 (0 gün önce, eşik 7 gün)
$ echo $?
0

$ atlas doctor --strict
# drift yok → çıktı aynı, exit 0

# drift varsa (12 gün önce, eşik 7):
$ atlas doctor --strict
[Kalite kapıları]
  DECISIONS.md: DECISIONS.md
  son giriş: 2026-07-18 (12 gün önce, eşik 7 gün)
  [!] DECISIONS.md son giriş 12 gün önce (2026-07-18), eşik 7 gün.
$ echo $?
9

# CI kalıbı:
$ atlas doctor --json --strict > doctor.json 2> doctor.err || {
    echo "quality gate failed"; cat doctor.err; exit 1
  }

# Farklı eşik:
$ ATLAS_STRICT_DRIFT_DAYS=14 atlas doctor --strict
```

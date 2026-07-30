# 032.1 — Ship

## Sonuç
- **`quality.entry_count`:** DECISIONS.md'de son 30 gün içindeki
  `^## YYYY-MM-DD` başlık sayısı. `count < min_entries` → uyarı.
  Env: `ATLAS_STRICT_ENTRY_WINDOW_DAYS` (30), `ATLAS_STRICT_MIN_ENTRIES`
  (1). Fail-safe parse (018/026 kalıbı).
- **`quality.vault_health`:** vault dizini var mı + en az 1 `.md`
  içeriyor mu. Yoksa/boşsa uyarı. Vault yolu `_vault_root()`
  (mevcut env sözleşmesi).
- **Rapor entegrasyonu:** `_collect_doctor_report`'ta `quality`
  bölümü 3 alanla döner: `decisions_drift` (032) + `entry_count`
  (yeni) + `vault_health` (yeni).
- **İnsan format:** `[Kalite kapıları]` bölümüne 2 alt satır
  eklendi:
  ```
  son 30 günde giriş: 57 (min 1)
  vault: vault (7 not)
  ```
  Uyarı varsa `[!]` prefix.
- **Tek kanaldan strict exit 9:** `_has_quality_warning(report)`
  yardımcısı — `quality.*` altındaki herhangi bir `warning`
  doluysa `--strict` iken exit 9. Hem insan hem JSON yolunda
  aynı kural. Kullanıcı "3 farklı bulgu, 3 farklı exit kodu"
  yerine tek "kalite gate" görür.
- **JSON şeması:** eski alanlar korundu; yeni iki alan eklendi
  (`entry_count`, `vault_health`). Eski JSON tüketicileri hâlâ
  eski alanları görür.
- **Bit-uyumluluk:** `--strict` yoksa tüm uyarılar bilgi amaçlı
  görünür, exit 0 (mevcut davranış).

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_read_strict_entry_env,
                                            +_count_recent_decisions,
                                            +_check_vault_health,
                                            +_has_quality_warning;
                                            _collect_doctor_report
                                              quality 3 alanlı;
                                            _cmd_doctor insan format
                                              ek 4 satır + JSON+strict
                                              tek kanal via
                                              _has_quality_warning)
tests/test_cli_doctor_strict.py           (edit: +10 test 032.1:
                                            entry_count x4, vault x3,
                                            strict entry/vault/JSON;
                                            mevcut "temiz exit 0"
                                            testi vault+.md ekler
                                            (yeni sözleşme))
pipeline/tasks/032-1-doctor-strict-plus/*.md  (2 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_doctor` mevcut çıktı + JSON alanları KORUNDU (yalnız
  EKLEMELER).
- `_check_decisions_drift` (032) davranışı değişmedi.
- `_collect_doctor_report` şema: `quality` alt-bölümleri genişledi;
  eski `decisions_drift` alanı birebir aynı.
- **Sözleşme değişikliği (davranışsal):** `--strict` artık üç
  kanaldan tetiklenir. Kullanıcı `atlas hooks install` ile pre-commit
  kurulmuşsa 034 shim bunu yakalar. Öncekilerde tek kanal (drift)
  olduğu için "temiz" tanımı vault + entry_count'u gerektirmezdi.
  Test suite güncellendi.

## Kalite kapıları
- pytest: **656 passed + 12 skipped** (646 → +10)
- coverage: %90.97 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/032.1-doctor-strict-plus` — 034 üstünde tek commit.

## Env sözleşmesi (yeni ★)
| Değişken | Anlam |
|---|---|
| `ATLAS_STRICT_ENTRY_WINDOW_DAYS` ★ | **032.1** — entry count denetim penceresi (varsayılan 30 gün) |
| `ATLAS_STRICT_MIN_ENTRIES` ★ | **032.1** — pencere içinde beklenen minimum giriş (varsayılan 1) |

## Kullanım örneği
```bash
$ atlas doctor
=== ATLAS doctor — env sağlık kontrolü ===
...
[Kalite kapıları]
  DECISIONS.md: DECISIONS.md
  son giriş: 2026-07-30 (0 gün önce, eşik 7 gün)
  son 30 günde giriş: 57 (min 1)
  vault: vault (7 not)

# Aktif proje: hepsi temiz, exit 0.

# Sabık drift + sessiz proje senaryosu:
$ ATLAS_STRICT_ENTRY_WINDOW_DAYS=7 ATLAS_STRICT_MIN_ENTRIES=3 \
    atlas doctor --strict
[Kalite kapıları]
  son giriş: 2026-07-28 (2 gün önce, eşik 7 gün)
  [!] DECISIONS son 7 günde 1 giriş, minimum 3.
  vault: vault (7 not)
$ echo $?
9  # entry_count uyarısı üzerinden

# CI kalıbı (JSON + strict):
$ atlas doctor --json --strict > doctor.json 2> quality.err || {
    echo "quality gate failed"; cat quality.err; exit 1
  }
```

## Not
032.1 pre-commit hook (034) ile birlikte çalışır — kullanıcı
`atlas hooks install` yapmışsa her commit'te drift + entry_count +
vault_health denetimi otomatik kesiyor. Manuel çalıştırma da mümkün
(`atlas doctor --strict`).

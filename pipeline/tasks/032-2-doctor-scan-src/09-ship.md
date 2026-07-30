# 032.2 — Ship

## Sonuç
- **`atlas doctor --scan-src [PATH]`** opt-in bayrağı — kaynak
  dizinine `scan_secrets` uygular. Varsayılan PATH: `src`.
- **`_check_scan_src(path)` yardımcısı:** dosya-bazlı tara, bulgu
  sayısı + ilk 5 dosya özet + `warning` (>0 ise).
- **Rapor entegrasyonu:** `--scan-src` verildiğinde `quality.scan_src`
  alanı EKLENİR; verilmezse hiç yer almaz (**bit-uyumluluk** +
  ekstra IO yok).
- **İnsan format:** bayrak verildiğinde `[Kalite kapıları]` altına
  `sır taraması: <path> (<N> bulgu)` satırı; bulgu varsa `[!]` prefix.
- **Strict davranışı:** `_has_quality_warning(report)` (032.1) zaten
  `quality.*.warning` alanlarına bakıyor — `scan_src.warning` de
  otomatik yakalanır, ayrı bir yol gerekmedi. Tek kanal, dört kaynak
  (drift + entry_count + vault + scan_src).
- **Hook shim v2:** `tools/hooks/pre-commit` tek satır komut:
  `atlas doctor --strict --scan-src`. İki subprocess → tek. `_HOOK_
  SIGNATURE` v1 kalmaya devam ediyor (imza prefix eşleşmesi kullanır);
  eski v1 shim'i kurulu kullanıcılar `atlas hooks install` çağırırsa
  sessiz v2'ye güncellenir (034 mekanizması: ATLAS imzalı ama farklı
  içerik = güncelleme).
- **`atlas scan <path>` komutu SÖZLEŞMESİ DEĞİŞMEDİ** — bağımsız
  kullanım devam ediyor; `_cmd_scan` dokunulmadı.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_check_scan_src;
                                            _collect_doctor_report'a
                                              scan_src_path parametresi
                                              opsiyonel + quality.scan_src
                                              alanı bayrak varsa;
                                            _cmd_doctor --scan-src parse
                                              + insan format satır +
                                              docstring;
                                            parser --scan-src nargs='?'
                                              const='src')
tools/hooks/pre-commit                    (edit: v1 → v2, tek komut
                                            `atlas doctor --strict
                                            --scan-src`)
tests/test_cli_doctor_strict.py           (edit: +7 test 032.2:
                                            scan_src yok alan yok
                                            (bit-uyumluluk), bayrak
                                            temiz, sır bulundu warning,
                                            strict+sır exit 9, dizin
                                            yok warning, insan format,
                                            atlas scan komutu korundu)
pipeline/tasks/032-2-doctor-scan-src/*.md (2 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_doctor` mevcut çıktı KORUNDU; yalnız EKLEMELER.
- `_collect_doctor_report` şema: opsiyonel `scan_src_path` parametresi
  eklendi (default None, geri uyumlu); `quality.scan_src` alanı
  yalnız istenirse görünür.
- `_cmd_scan` (mevcut `atlas scan`) hiç dokunulmadı; regresyon test
  bunu doğrular.
- `_has_quality_warning` (032.1) davranışı değişmedi — otomatik
  `scan_src.warning`'i de yakaladı, ekstra kod gerekmedi.
- Hook shim v2 aynı imza prefix'iyle uyumlu (uninstall güvence).

## Kalite kapıları
- pytest: **670 passed + 12 skipped** (663 → +7)
- coverage: %90.99 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/032.2-doctor-scan-src` — 034.1 üstünde tek commit.

## Env sözleşmesi
Değişmedi.

## Kullanım örneği
```bash
$ atlas doctor --scan-src
=== ATLAS doctor — env sağlık kontrolü ===
...
[Kalite kapıları]
  DECISIONS.md: DECISIONS.md
  son giriş: 2026-07-30 (0 gün önce, eşik 7 gün)
  son 30 günde giriş: 60 (min 1)
  vault: vault (7 not)
  sır taraması: src (0 bulgu)

# Sır varsa:
$ atlas doctor --scan-src --strict
...
  sır taraması: src (2 bulgu)
  [!] scan 2 olası sır buldu (src); ilk dosya(lar): src/config.py, src/legacy.py
$ echo $?
9

# Farklı yol:
$ atlas doctor --scan-src tests --strict

# Hook v2 (install ile otomatik güncellenir):
$ atlas hooks install
hooks: kuruldu -> .git/hooks/pre-commit
# Her commit'te tek quality gate koşar.
```

## Meta
032 hook mekanı üzerine 032.1 (üç kanal) + 032.2 (dördüncü kanal)
katmanlarıyla artık **tek `atlas doctor --strict --scan-src` çağrısı**
DECISIONS drift + entry count + vault health + sır taraması bulgusunu
tek exit 9 üzerinden kesiyor. Pre-commit hook zinciri v2 ile temiz —
iki subprocess yerine tek.

# 032.3 — Ship

## Sonuç
- **`_iter_scan_hits(path) -> list[tuple[Path, str, str]]`** yeni
  ortak yardımcı. Her tuple `(dosya_yolu, sır_ismi, maskeli_değer)`.
  Path yoksa boş liste; okuma hataları sessiz atla.
- **`_cmd_scan` refactor:** `_iter_scan_hits` kullanır. Çıktı
  sözleşmesi (stdout satır formatı + stderr uyarı + exit 0/1) BİREBİR
  korundu. Regresyon: mevcut `test_scan_sir_bulur` + `test_scan_temiz`
  aynen geçiyor.
- **`_check_scan_src` refactor:** `_iter_scan_hits` kullanır. Yeni
  ek: **sample_files unique** (bir dosyada çok bulgu varsa aynı dosya
  iki kez basılmaz). `path.exists()` kontrolü kendisinde kalır çünkü
  "scan hedefi yok" uyarı gövdesi özel.
- **Dönüş tipi neden `list`, `Iterable` değil:** hem `_cmd_scan`
  (`len(hits)` gerekli) hem `_check_scan_src` (`total` + unique sample)
  tam liste ister; iterator tekrar tüketilemez.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_iter_scan_hits DRY
                                            yardımcısı; _cmd_scan +
                                            _check_scan_src bunu tüketir;
                                            _check_scan_src sample_files
                                            unique (bugfix))
tests/test_cli_doctor_strict.py           (+6 test 032.3:
                                            _iter_scan_hits doğrudan x5
                                            (dizin yok, bir bulgu, çoklu
                                            dosya, tek dosya arg, okuma
                                            hatası); _check_scan_src
                                            unique sample bugfix testi)
pipeline/tasks/032-3-scan-dry/*.md        (2 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_scan` çıktı sözleşmesi (stdout satır formatı + stderr uyarı
  + exit 0/1) BİREBİR korundu.
- `_check_scan_src` dönüş şeması BİREBİR korundu (küçük iyileşme:
  sample_files bir dosyayı iki kez saymaz — önceki sürümde de aslında
  saymıyordu ama garantisiz).
- Mevcut 2 scan test + 7 032.2 test aynen geçiyor.

## Kalite kapıları
- pytest: **676 passed + 12 skipped** (670 → +6)
- coverage: %91.17 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/032.3-scan-dry` — main üstünde tek commit.

## Env sözleşmesi
Değişmedi. Yeni exit kodu YOK.

## Kullanım örneği
```bash
# İki komut da aynı motoru (`_iter_scan_hits`) kullanır:
$ atlas scan src
Sır bulunamadı.

$ atlas doctor --scan-src
...
[Kalite kapıları]
  sır taraması: src (0 bulgu)
```

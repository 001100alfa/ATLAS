# 032.3 — İhtiyaç: `scan_secrets` döngüsü DRY refactor

## Bağlam
032.2'de `_check_scan_src` eklendi ve `_cmd_scan` (atlas scan
komutu) ile arasında **aynı üç adımlı döngü** var:
1. Path.exists / is_file / rglob
2. Her dosya için `text = f.read_text(encoding="utf-8")` (UnicodeDecode
   ve OSError yakalama)
3. `for name, masked in scan_secrets(text)` — bulguları topla

İki yerde ayrı tutuldu — birinde print/exit, diğerinde dict/warning.
Bu tam bir DRY ihlali; bir tarafta bug varsa (encoding, path
handling), diğeri sessiz kalır.

## İhtiyaç (tek cümle)
`_iter_scan_hits(scan_path) -> list[tuple[Path, str, str]]` ortak
yardımcısına çık; `_cmd_scan` ve `_check_scan_src` bunu tüketsin;
davranış birebir korunsun.

## Ölçülebilir Başarı
- **M1 — `_iter_scan_hits(path) -> list[tuple[Path, str, str]]`:**
  Ortak yardımcı; her tuple `(dosya_yolu, sır_ismi, maskeli_değer)`.
  Path yoksa/is_file değilse rglob; okuma hataları sessiz atla.
  Boş liste döner path yoksa.
- **M2 — `_cmd_scan` refactor:** `_iter_scan_hits` kullanır; mevcut
  çıktı formatı **birebir korunur** (`{f}: {name} -> {masked}`
  her satır; sonda `N olası sır bulundu`).
- **M3 — `_check_scan_src` refactor:** `_iter_scan_hits` kullanır;
  ancak `path.exists()` kontrolü kendisinde kalır (özel warning
  gövdesi "scan hedefi yok"); mevcut şema birebir korunur.
- **M4 — Regresyon:** mevcut `tests/test_cli.py` scan testleri +
  `tests/test_cli_doctor_strict.py` 032.2 testleri değişmeden
  geçmeli.
- **M5 — Yeni test:** +2-3 test `_iter_scan_hits` doğrudan:
  dizin yok → [], bir bulgu → 1 tuple, birden çok dosyada bulgu →
  N tuple.
- **M6 — DECISIONS:** [KARAR] neden ortak yardımcı `Iterable` değil
  `list` döner (test edilebilirlik + tekrar tüketim); neden
  `_check_scan_src` `path.exists` kendisinde kalıyor (mesaj gövdesi
  farklı).

## Kapsam DIŞI
- `scan_secrets` API'sini değiştirmek — `security/audit.py` sözleşme.
- Custom scan config (ignore paterns) — YAGNI.
- Streaming iterator (`yield`) — dosya sayısı büyük olsa da tam
  liste tercih edilir çünkü hem `_cmd_scan` hem `_check_scan_src`
  toplam sayı ister; iterator iki kez tüketilemez.

## Kısıt
- `_cmd_scan` çıktı sözleşmesi (stdout satırları + stderr uyarı +
  exit kodu) BİREBİR korunur.
- `_check_scan_src` dönüş şeması BİREBİR korunur.
- Yeni env DEĞİL, yeni exit kodu YOK.
- Türkçe yorum.

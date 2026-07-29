# 029 — Ship

## Sonuç
- **Alarm bayrağı:** `atlas metrics --alert PCT` — `float`, 0–100.
  Verilmezse mevcut davranış (alarm yok, exit 0).
- **Eşik altı:** cache-hit oranı `< PCT` → `stderr`'e `UYARI: cache-hit
  %X.X < eşik %Y.Y` yazar ve **exit 8** döner.
- **Eşik üstü/eşit:** oran `>= PCT` → mevcut çıktı korunur, exit 0.
- **`--alert 0` kapatır:** 0 > 0 asla doğru olmaz, dolayısıyla alarm
  hiç ateşlenmez. Kayıtsız + `--alert 0` = exit 0 (kural: sıfır eşik
  = alarm devre dışı).
- **Kayıt yok:** metrics.jsonl boş/yoksa `hit_ratio = 0.0`; `--alert
  10` verilirse 0 < 10 olduğundan alarm ATEŞLENİR (kural: "veri yok
  = uyarıdır" — CI'da metrics dosyası eksikse sessiz kalmasın).
- **JSON uyumu:** `--json --alert 80` → JSON liste stdout'a basılır,
  UYARI stderr'e, exit kodu aynı kurala tabi. İki akış birbirine
  karışmaz — CI JSON'u parse ederken uyarıyı ayrıca gözler.
- **Sınır dışı:** `--alert 150` veya `--alert -5` → `SPEC HATASI:
  --alert 0–100 aralığında olmalı` + exit 2.
- **Yeni exit kodu:** **8** = "alert eşiği geçilemedi" (`atlas
  metrics` özelinde). 6 zaten "archive-all failed"; semantik
  karıştırılmadı.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: _cmd_metrics --alert
                                            sınır kontrolü + eşik hesabı
                                            + stderr UYARI + exit 8;
                                            parser p_met --alert float)
tests/test_cli_metrics.py                 (+6 test: alt geçer, üst
                                            düşer, kayıtsız düşer, sıfır
                                            kapatır, --json birleşir,
                                            sınır dışı exit 2)
pipeline/tasks/029-metrics-alert/*.md     (2 artefakt: 00-need, 09-ship)
```

## Sözleşme değişmezliği
- `_cmd_metrics` insan formatı çıktısı ve `--json` çıktısı birebir
  korundu — hiçbir alan silinmedi, hiçbir satır değişmedi.
- Alarm olmadan (`--alert` yok) exit kodu her zaman 0 (mevcut).
- `--limit` etkileşimi değişmedi — tail üzerinden hesap.
- Yeni env DEĞİŞKENİ YOK.

## Kalite kapıları
- pytest: **557 passed** (551 → +6)
- coverage: %91.35 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/029-metrics-alert` — 028 üstünde tek commit.

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
| **8** ★ | **029 — `atlas metrics --alert` eşik altı** |

## Kullanım örneği
```bash
$ atlas metrics --alert 20
=== ATLAS metrics — son 20 çağrı ===
  toplam: 12 çağrı
  ...
  cache-hit oranı: 62.5% (500 / 800)
  ...
$ echo $?
0

$ atlas metrics --alert 80
=== ATLAS metrics — son 20 çağrı ===
  ...
  cache-hit oranı: 62.5% (500 / 800)
  ...
UYARI: cache-hit %62.5 < eşik %80.0    # stderr
$ echo $?
8

# CI'da:
$ atlas metrics --alert 40 --json > metrics.json 2> alerts.txt || {
    cat alerts.txt >&2
    exit 1
  }
```

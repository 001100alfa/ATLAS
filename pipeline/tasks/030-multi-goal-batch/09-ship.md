# 030 — Ship

## Sonuç
- **CLI:** `--goal-file` `nargs='+'`; birden fazla dosya batch,
  bir dosya bit-uyumlu tek görev (027 davranışı).
- **Fail-fast (varsayılan):** ilk `_cmd_run_goal` başarısızlığı
  (rc != 0) → sonraki goal'ler `atlandı (fail-fast)` işaretlenir,
  çalıştırılmaz.
- **`--continue-on-error`:** tüm goal'ler çalışır; hatalar özet
  tablosunda görünür, exit kodu en yüksek hatayı verir.
- **Run-id çakışma çözümü:**
  - `--run-id X` verildi → her goal `X_1`, `X_2`, ... `X_N`.
  - Yoksa timestamp bir kez alınır → `<TS>_1`, `<TS>_2`, ...
  - Tek dosya (N=1) → suffix YOK, 027 davranışı bit-uyumlu.
- **Özet tablosu (stdout, batch sonunda):**
  ```
  === ATLAS batch özeti — 3 goal ===
    1. a                       + done   (run_id=R_1)
    2. b                       x exit=4 (run_id=R_2)
    3. c                       - atlandı (fail-fast)
  batch exit: 4
  ```
- **Exit kodu:** hepsi 0 → 0; aksi `max(rc for rc in codes)`. CI
  script `set -e` semantiği: batch exit != 0 = en az bir hata.
- **--dry-run + batch:** tek bayrak, tüm goal'lere uygulanır;
  batch mod başlığında `+ dry-run` göründü.
- **Tek dosya bit-uyumluluğu:** `atlas run --goal-file X.yaml`
  (N=1) çağrısı özet tablosu BASMAZ, 027 davranışı birebir aynı.
- **Boş liste:** `--goal-file` sonrası argüman yok → argparse
  SystemExit 2 (mevcut sözleşme).

## Dosyalar
```
src/atlas_core/cli.py                     (edit: --goal-file nargs='+',
                                            +--continue-on-error,
                                            _cmd_run dispatch (N==1 →
                                              tek dosya, N>1 → batch);
                                            +_cmd_run_batch: fail-fast,
                                              run-id suffix, özet tablo,
                                              max exit)
tests/test_cli_batch.py                   (yeni, +8 test:
                                            bit-uyumlu, iki başarılı,
                                            fail-fast atlar, continue-on-error,
                                            exit=max, timestamp suffix,
                                            dry-run hepsine, boş liste)
pipeline/tasks/030-multi-goal-batch/*.md  (2 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_run_goal` sözleşmesi KORUNDU — batch onu N kez çağırır.
- `_cmd_run` echo demo yolu (goal_file yok) KORUNDU.
- Tek `--goal-file X` çağrısı 027 ile birebir (özet tablo YOK,
  run-id suffix YOK).
- `_cmd_replay` → `_cmd_run_goal` yolu değişmedi (replay yine tek
  goal_file str geçer).

## Kalite kapıları
- pytest: **600 passed + 8 skipped** (592 → +8; 8 skip 026.1/026.2
  platform-specific)
- coverage: %91.19 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/030-multi-goal-batch` — 026.2 üstünde tek commit.

## Env sözleşmesi
Değişmedi.

## Kullanım örneği
```bash
# CI regresyon matrisi:
$ atlas run --goal-file tests/goals/build.yaml \
                       tests/goals/test.yaml \
                       tests/goals/lint.yaml \
            --run-id ci-run-42
# Fail-fast: build başarısız olursa test/lint atlanır.
# Ya da:
$ atlas run --goal-file tests/goals/*.yaml --continue-on-error
# Tümünü çalıştır, sonda tabloda hataları gör.

# Batch dry-run:
$ atlas run --goal-file a.yaml b.yaml c.yaml --dry-run
```

## Not (DECISIONS'e blok)
- Fail-fast neden varsayılan: `set -e` shell semantiği + CI erken
  hata bildirimi. `--continue-on-error` opt-in — bilinçli tercih.
- Run-id suffix `_<i>` neden `_1/_2` yerine sıra numarası: 100
  goal olursa `_1/_2/../_100` sıralama kolay; timestamp base zaten
  saniye ayrımı verir.
- Exit kodu `max(rc)`: kod büyüklüğü hata ağırlığını yansıtır (2
  = SPEC HATASI < 4 = done=False < 5 = denied < 7 = env hata).
  Kullanıcı en kötü hatayı görür.

# 028 — Ship

## Sonuç
- **Liste komutu:** `atlas replay --list` `.atlas/runs/*.yaml`
  dosyalarını **mtime azalan** sırayla listeler. Her satır: `#`,
  `run_id` (32 char), `mtime` (YYYY-MM-DD HH:MM:SS), `goal` (60 char).
- **JSON çıktı:** `atlas replay --list --json` `[{run_id, mtime,
  goal}, ...]` verir; JSON-only tüketicilere uygun.
- **Limit:** `atlas replay --list --limit N` (varsayılan 20). En yeni
  N kayıt.
- **Yaml-dışı yoksay:** `.txt`, `.yml`, alt dizin gibi kayıtlar
  listeye girmez — yalnız `.yaml` uzantılı ve `is_file()` olanlar.
- **Boş kayıt:** klasör yok veya boşsa `(hiç kayıt yok)` + exit 0
  (hata değil).
- **Arg hatası:** `atlas replay` (positional yok, `--list` yok) →
  `SPEC HATASI: run-id ya da --list gerekli` + exit 2.
- **027 uyumluluğu:** `atlas replay <run-id>` sözleşmesi birebir
  korunur — yalnız positional `nargs='?'` oldu; verildiğinde 027
  akışı çalışır.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_extract_goal_from_yaml,
                                            +_collect_replay_runs,
                                            +_cmd_replay_list;
                                            _cmd_replay --list dallanması;
                                            parser --list/--json/--limit +
                                            run_id nargs='?')
tests/test_cli_replay.py                  (+6 test: boş, mtime desc,
                                            JSON, limit, yaml-dışı yoksay,
                                            arg hatası)
pipeline/tasks/028-replay-list/*.md       (2 artefakt: 00-need, 09-ship)
```

## Sözleşme değişmezliği
- `_cmd_replay` sözleşmesi korundu (`--list` yeni bayrak, mevcut
  akış değişmedi).
- `atlas replay <run-id>` positional çağrısı çalışır.
- `ATLAS_RUNS_DIR` env override davranışı 027 ile aynı.
- Yeni env DEĞİŞKENİ YOK.
- Yeni exit kodu YOK — 2 (SPEC HATASI) mevcut sözleşme.

## Kalite kapıları
- pytest: **551 passed** (545 → +6)
- coverage: %91.32 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/028-replay-list` — main üstünde tek commit.

## Env sözleşmesi
Değişmedi.

## Kullanım örneği
```bash
$ atlas replay --list
=== ATLAS replay — kayıtlı 3 run ===

  #   run_id                           mtime                goal
  1   gorev-second                     2026-07-29 14:22:10  ikinci deneme
  2   gorev-first                      2026-07-29 14:20:03  ilk çalışma
  3   demo-orig                        2026-07-29 09:15:00  demo hedefi

$ atlas replay --list --json --limit 1
[{"run_id": "gorev-second", "mtime": "2026-07-29 14:22:10", "goal": "ikinci deneme"}]

$ atlas replay gorev-first --new-run-id retry
# (027 davranışı — kopyayı yükle + yeniden çalıştır)
```

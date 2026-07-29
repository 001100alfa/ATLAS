# 027 — Ship

## Sonuç
- **YAML kopyalama:** `atlas run --goal-file X.yaml` her başarılı
  başlangıçta YAML'ı `.atlas/runs/<goal-id>.yaml` olarak kopyalar
  (`goal-id = <yaml stem>-<run-id>`).
- **Replay komutu:** `atlas replay <run-id>` kopyayı bulur, yeni
  bir run-id (varsayılan timestamp) ile `_cmd_run_goal`'a iletir.
- **Env override:** `ATLAS_RUNS_DIR` (varsayılan `.atlas/runs`).
- **Dashboard entegrasyonu:** dashboard tablosuna `run_id` kolonu
  eklendi; `.atlas/runs/*.yaml` dosyaları mtime desc sırayla runs
  listesiyle hizalanır.
- **Hata dallanması:** kopya yoksa `SPEC HATASI: run bulunamadı:
  <id>` + exit 2.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_runs_dir,
                                            +_archive_goal_yaml,
                                            +_cmd_replay;
                                            _cmd_run_goal YAML kopyalar;
                                            dashboard run_id kolonu;
                                            parser "replay" alt-komutu)
tests/test_cli_replay.py                  (yeni, 6 test — kopya oluşur,
                                            replay çalışır, yoksa exit 2,
                                            RUNS_DIR override, dashboard
                                            run_id kolonu, JSON çıktıda alan)
pipeline/tasks/027-atlas-replay/*.md      (5 artefakt)
```

## Sözleşme değişmezliği
- `_cmd_run_goal` sözleşmesi korundu.
- `atlas run --goal-file X --run-id ID` mevcut arg akışı korunur.
- `atlas dashboard` mevcut kolonlar korundu; `run_id` sona eklendi.

## Kalite kapıları
- pytest: **545 passed** (539 → +6)
- mypy strict + ruff: temiz

## Branch
`feat/027-atlas-replay` — 026 üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_RUNS_DIR` | Replay kopyaları yol override (varsayılan `.atlas/runs`) |

## Kullanım örneği
```bash
$ atlas run --goal-file gorev.yaml --run-id first
# .atlas/runs/gorev-first.yaml oluştu

$ atlas dashboard
=== ATLAS dashboard — son 10 run ===

  #   ts                   exit  steps  run_id                    cost
  1   2026-07-29 10:00:00  done  1      gorev-first               $0.012

$ atlas replay gorev-first --new-run-id retry
# .atlas/sandbox/gorev-first-retry/ altında yeniden çalışır
```

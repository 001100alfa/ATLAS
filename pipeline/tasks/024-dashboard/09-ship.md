# 024 — Ship

## Sonuç
`atlas dashboard [--limit N] [--json]` — `.atlas/audit.jsonl` +
`.atlas/metrics.jsonl` özet. Son N `atlas-run` oturumunu tablo
halinde gösterir: `start_ts`, `exit` (done/max_steps/denied/llm_error),
plan sayısı, tahmini cost (run zaman aralığındaki metrics'e göre).

- İlk satır: `denetim zinciri: GEÇERLİ / BOZULMUŞ` (`AuditLog.verify`).
- Bitmemiş run'lar `unfinished` olarak işaretlenir.
- Read-only, exit 0.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_collect_runs_from_audit
                                            heuristik + _cost_for_run
                                            zaman aralığı hesabı +
                                            _cmd_dashboard tablosu/JSON)
tests/test_cli_dashboard.py               (yeni, 6 test)
pipeline/tasks/024-dashboard/*.md         (5 artefakt)
```

## Sözleşme değişmezliği
- `AuditLog` ve mevcut alt-komutlar dokunulmadı.
- Yeni exit kodu YOK.

## Kalite kapıları
- pytest: **518 passed** (512 → +6)
- mypy strict + ruff: temiz
- `atlas scan src`: sır yok

## Branch
`feat/024-dashboard` — 023 üstünde tek commit.

## Kullanım örneği
```bash
$ atlas dashboard --limit 5
denetim zinciri: GEÇERLİ

=== ATLAS dashboard — son 5 run ===

  #   ts                   exit         steps  cost
  1   2026-07-29 10:00:00  done         3      $0.012000
  2   2026-07-29 10:15:00  max_steps    8      $0.045000
  3   2026-07-29 10:30:00  llm_error    0      ?
```

```bash
$ atlas dashboard --json | jq '.runs | length'
5
```

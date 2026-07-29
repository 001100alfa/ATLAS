# 023 — Ship

## Sonuç
Anthropic çağrılarının usage'ı `.atlas/metrics.jsonl`'a append edilir
(tek satır JSON: `{ts, in, out, cache_c, cache_r, cost}`). Yeni
`atlas metrics [--limit N] [--json]` alt-komutu son N kaydı özetler:
toplam tokens, cache-hit oranı %, tahmini cost.

- Streaming (019) ve non-streaming yol her ikisinde de yazım aktif.
- Yazım hatası **sessiz** — disk dolu / izin yoksa plan akışı devam eder.
- `ATLAS_METRICS` env yol override.

## Dosyalar
```
src/atlas_core/orchestrator/planner.py    (edit: +_metrics_path,
                                            +_write_metric_for_data;
                                            _call_anthropic her iki yolda çağırır)
src/atlas_core/cli.py                     (edit: +_cmd_metrics;
                                            parser "metrics" alt-komutu)
tests/test_cli_metrics.py                 (yeni, 7 test)
pipeline/tasks/023-cache-metrics/*.md     (5 artefakt)
```

## Sözleşme değişmezliği
- `_call_anthropic` imzası korundu; yalnız yan-etki eklendi.
- `Planner`, `make_planner`, `LLMPlannerError` — dokunulmadı.
- claude/acp backend'ler metric yazmaz (usage native değil).

## Kalite kapıları
- pytest: **512 passed** (505 → +7)
- mypy strict + ruff: temiz

## Branch
`feat/023-cache-metrics` — 022 üstünde tek commit.

## Env sözleşmesi (yeni)
| Değişken | Anlam |
|---|---|
| `ATLAS_METRICS` | metrics.jsonl yolu override (varsayılan `.atlas/metrics.jsonl`) |

## Kullanım örneği
```bash
# 20 çağrıdan sonra
$ atlas metrics
=== ATLAS metrics — son 20 çağrı ===
  toplam: 20 çağrı
  input tokens:   1234
  output tokens:  567
  cache creation: 100
  cache read:     3000
  cache-hit oranı: 69.2% (3000 / 4334)
  tahmini cost:   $0.006543

# CI script'i için JSON
$ atlas metrics --json | jq 'length'
20
```

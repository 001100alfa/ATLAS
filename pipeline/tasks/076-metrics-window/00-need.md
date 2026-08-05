# Görev 076 — İhtiyaç

SPEC 023 `atlas metrics --limit N` son N kaydı özetliyor. Ama cron
`*/5 * * * *` "son 5 dk metriği" bekliyor — count-based değil
time-based. Kullanıcı `--limit 100` yazınca eski kayıtlar da girer.

## Kabul

- `atlas metrics --window MINUTES [--limit N]`:
  - `ts` alanı ISO 8601 parse; `now - MINUTES` sonrasındaki kayıtlar.
  - `ts` yok/bozuk → nazik dahil (defensive).
  - `--limit` ile ORTOGONAL: önce window filtresi, sonra son N slice.
  - `--window <= 0` → exit 2 SPEC HATASI.
- `--json`, `--alert`, `--alert-email`, `--alert-webhook`, `--alert-slack`,
  `--format prometheus`, `--serve` mevcut bayraklar bit-uyumlu (window
  ortogonal — filtre records üzerinde).

## Risk

- `datetime.fromisoformat` Python 3.11+ mikrosaniye + timezone parse
  eder. Planner `isoformat(timespec="seconds")` timezone-naive local
  yazıyor; window da naive → tutarlı.
- Prometheus text (`_build_metrics_prometheus_text`) window uygulamaz —
  scrape hedefi live, `limit` yeterli.

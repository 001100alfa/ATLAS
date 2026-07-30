# Görev 031.1 — Teslim

Batch `--dry-run` modunda özet tablosunun altına toplu step
agregasyonu eklendi (hem seri hem paralel dal).

## Uygulama
- `_summarize_dry_run_captures(captures)`: regex parse; `total_steps`,
  `by_kind`, `actions` alanlı dict.
- `_print_dry_run_summary(s)`: insan formatı özet.
- Seri döngü: `_Tee(sys.stdout, buf)` ile `contextlib.redirect_stdout`
  altında `_cmd_run_goal` çağrısı; buf sonda özet için parse edilir.
- Paralel dal: mevcut TLS-captured metinler `captured_outputs`
  listesine eklenir.

## Kanıtlar
- Seri dry-run: özet başlığı + `toplam step:` + `plan=`, `act=`
- Paralel dry-run: özet başlığı + `toplam step:`
- `--dry-run` YOK: özet BASILMAZ
- `_summarize_dry_run_captures` birim: 6 step, 2 plan, 2 act, 1 observe,
  1 reflect
- +4 test (726 yeşil, cov %90.58)

## Değişmeyen sözleşme
- Mevcut SPEC 030 + 031 testleri geçiyor.
- `--dry-run` YOK durum bit-uyumlu.

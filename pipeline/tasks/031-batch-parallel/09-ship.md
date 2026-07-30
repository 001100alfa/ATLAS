# Görev 031 — Teslim

`atlas run --goal-file A B C --jobs N` paralel batch (SPEC 030
uzantısı). N=1 seri (bit-uyumlu); N>1 ThreadPoolExecutor.

## Uygulama
- **`_ThreadCaptureStream`** (cli.py): TLS StringIO — her thread için
  ayrı buf, ana thread'in print'i etkilenmez. `sys.stdout`/`sys.stderr`
  paralel süresi boyunca instance ile değiştirilir, `finally`'de eski
  haline döner.
- **`_run_single_goal_captured`**: worker fonksiyonu; capture stream
  `.begin()/.end()` ile stdout+stderr yakalar.
- **`_cmd_run_batch`**: N>1 dalı `ThreadPoolExecutor(max_workers=N)`
  + `as_completed` (sonuçları başlangıç sırasına göre topla) + döngü
  sırasında worker output'unu blok halinde bas.
- **AuditLog thread-safety** (audit.py): `_lock_for(path)` module-level
  path bazlı lock; `record()` içi kilit + `verify()` boş satır fail-safe.

## Yeni bayrak
- `--jobs N` (varsayılan 1). Geçersiz (< 1) → SPEC HATASI + exit 2.

## Yeni sözleşme
- Paralel modda **fail-fast implicit KAPALI** (continue-on-error);
  kullanıcı seri istiyorsa `--jobs 1`.
- LLM rate limit doğrudan `--jobs N` inflight sınırı — ekstra env YOK.

## Kanıtlar
- N=1 mevcut fail-fast korundu (`test_030_fail_fast_ilk_hata_kalanlari_atlar`)
- N=2 iki başarı → exit 0, 2 done
- N=2 fail-fast implicit off → 3 goal tümü çalışır, exit=max
- Log karışmaz: `[1/N] a` önce, `[2/N] b` sonra
- `--jobs 0` → exit 2 + SPEC HATASI
- `--jobs 5` küçük liste → 2 done
- +6 test (699 yeşil, cov %90.95)

## Değişmeyen sözleşme
- SPEC 030 testleri (7 test) bit-uyumlu geçiyor.
- `_cmd_run_goal` dokunulmadı.

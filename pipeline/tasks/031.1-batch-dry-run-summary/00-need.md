# Görev 031.1 — İhtiyaç

`atlas run --goal-file A B C --dry-run` her worker'ın plan step'lerini
tek tek basıyor. 5 goal + 4 step = 20 satır; kullanıcı toplu görünüm
istiyor (kaç step, hangi eylem türleri, temsili örnekler).

## Kabul kriteri
- `--dry-run` verildiğinde batch özet tablosundan sonra
  `=== ATLAS batch dry-run özeti ===` bloğu basılır.
- İçerik: `toplam step: N (plan=X, act=Y, observe=Z, reflect=W)` +
  ilk 5 act eylem metni.
- `--dry-run` YOKKEN özet BASILMAZ (bit-uyumluluk).
- Hem seri (`--jobs 1`) hem paralel (`--jobs N>1`) dallarda çalışır.
- Seri modda tee-capture (real-time stdout + buf) — mevcut çıktı sırası
  KORUNUR.

## Riskli
- Seride `contextlib.redirect_stdout(_Tee(...))` — tek thread, process-global
  redirect zararsız. Batch-parallel dry-run zaten TLS capture kullanıyor.
- Regex parse: `_cmd_run_goal` çıktı formatı sabit varsayılıyor
  (`  <kind:<8s> <text>`). Format değişirse özet 0 döner (bozulmaz,
  sessiz).

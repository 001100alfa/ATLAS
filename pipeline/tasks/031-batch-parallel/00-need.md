# Görev 031 — İhtiyaç

SPEC 030 batch (`atlas run --goal-file A B C`) SERİ çalışıyor. N goal
= N × ortalama süre. IO/LLM bound işlerde paralel çalıştırma ciddi
kazanç sağlar.

## Kabul kriteri
- `--jobs N` bayrağı (varsayılan 1).
- N == 1 → mevcut seri davranış BİT-UYUMLU (SPEC 030 testleri geçer).
- N > 1 → `ThreadPoolExecutor(max_workers=N)`.
- Fail-fast paralel modda anlamsız — worker'lar zaten koşuyor; implicit
  `continue-on-error` (tümü çalışır, sözleşmede belgelendi).
- Log satırları karışmaz: her worker `sys.stdout`'unu **thread-local
  StringIO**'ya yakalar, ana thread sonuçları sırayla basar.
- Exit kodu: max(exit_i) — SPEC 030 ile aynı.
- Sandbox path çakışması: her goal `<name>-<run_id_i>` alt-dizini alır
  (mevcut sözleşme), çakışma yok.
- `--jobs 0` veya negatif → SPEC HATASI + exit 2.
- Audit log thread-safe: `AuditLog` içi path bazlı module-level lock
  (aynı `audit.jsonl`'e yazan tüm thread'ler serileşir).

## Riskli
- **stdout redirect thread-safety**: `contextlib.redirect_stdout`
  process-global; iki thread aynı anda sys.stdout override etti mi
  ana thread'in print'i de buf'a düşer. Çözüm: kendi
  `_ThreadCaptureStream` (TLS StringIO) — her thread için ayrı buf,
  TLS'de buf yoksa gerçek stream'e yaz.
- **audit hash zinciri race**: `record()` prev_hash oku → yeni hash
  yaz → dosyaya append. İki thread aynı prev'i alırsa zincir bozulur.
  Çözüm: `_lock_for(path)` module-level lock (path bazlı).
- **LLM rate limit**: --jobs N doğrudan inflight sınırıdır (max N
  paralel LLM çağrısı). Kullanıcı N'i düşürerek API rate limit'e
  uyumlanır. Ekstra semafor YOK (basit tut).

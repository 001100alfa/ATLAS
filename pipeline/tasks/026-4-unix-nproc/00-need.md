# 026.4 — İhtiyaç: Unix MAX_PROC (RLIMIT_NPROC)

## Bağlam
Platform matrisinde tek boşluk kaldı: **Unix `MAX_PROC`**. Windows
Job Objects `ACTIVE_PROCESS` limitini 026.2'de karşılıyor, Unix
tarafında `RLIMIT_NPROC` bilinçli olarak dışarıda tutulmuştu (026.1
DECISIONS: "RLIMIT_CPU zaten fork bomb'u SIGXCPU ile keser").
Ancak platform simetrisi + net sözleşme adına, aynı env
(`ATLAS_SANDBOX_MAX_PROC`) Unix'te de RLIMIT_NPROC olarak uygulansın.

## İhtiyaç (tek cümle)
`ATLAS_SANDBOX_MAX_PROC` env verildiyse, Unix'te `_build_preexec_fn`
içine `resource.setrlimit(RLIMIT_NPROC, (n, n))` çağrısı eklensin;
Windows'ta zaten 026.2 Job ACTIVE_PROCESS ile karşılıyor.

## Ölçülebilir Başarı
- **M1 — Env sözleşmesi:** `ATLAS_SANDBOX_MAX_PROC` (026.2 ile ORTAK)
  — Unix'te `RLIMIT_NPROC`, Windows'ta Job `ACTIVE_PROCESS`.
  Kullanıcı sözleşmesi tam platform-agnostik olur.
- **M2 — Unix uygulama:** `_build_preexec_fn` içine `RLIMIT_NPROC`
  çağrısı eklenir. `getattr(_resource, "RLIMIT_NPROC", None)` ile
  koruma — bazı Unix dağıtımlarında sabit farklı olabilir (macOS'ta
  var, Linux'ta var, BSD'de var).
- **M3 — Env yoksa bit-uyumlu:** `MAX_PROC` yokken preexec_fn
  RLIMIT_NPROC çağırmaz. Mevcut 026.1 davranışı.
- **M4 — Windows sessiz no-op:** Windows'ta `_build_preexec_fn` HER
  ZAMAN None döner (026.1 kalıbı) — `MAX_PROC` Windows'ta 026.2
  Job Object yolu ile karşılanır.
- **M5 — Env parse hatası → yoksay:** `abc`/negatif/0 → RLIMIT_NPROC
  uygulanmaz (026.1 fail-safe kalıbı).
- **M6 — Test:** +3-4 test — `_build_preexec_fn` MAX_PROC ile
  callable döner (Unix mock), env parse ortak, RLIMIT_NPROC yok
  platform güvence.
- **M7 — DECISIONS:** [KARAR] neden 026.1'de bilerek dışarıda
  bırakılmıştı ve neden şimdi eklendi (semantik simetri); `getattr`
  koruma nedeni (platform-özel sabit); Unix canlı fork limit
  testinin CI-fragile olduğu ve mock ile doğrulama tercih.

## Kapsam DIŞI
- Unix canlı fork limit testi — CI ortamında (Ubuntu Actions
  runner) fork zaten sınırlı; testin deterministik olması zor.
  Mock ile `_build_preexec_fn`'in RLIMIT_NPROC parametre eklediği
  doğrulanır.
- macOS-özel davranış farkı — `RLIMIT_NPROC` macOS'ta da vardır,
  ekstra dallanma gerekmez.
- Cgroups (Linux) v2 nproc — daha karmaşık, container/user
  namespace gerektirir, YAGNI.
- `RLIMIT_NOFILE`, `RLIMIT_STACK` gibi ek limitler — YAGNI, ihtiyaç
  yok.

## Kısıt
- `_build_preexec_fn` mevcut imza korunur; içi genişler.
- `Action`, `make_action`, `ActionDeniedError` imzaları korunur.
- Env yokken bit-uyumlu 026.1 + 026.
- Test yalnız mock — canlı fork bomb yok.
- Windows'ta hiçbir davranış değişmez.

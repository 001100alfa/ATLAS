# 026.1 — İhtiyaç: Unix `resource` limitleri

## Bağlam
026 sandbox iyileştirmesi env whitelist + PATH + timeout + `shell=False`
uyguladı ama fork bomb / OOM'a karşı korumasız — 10 sn'de fork bomb
sistemi çökertir, `dd if=/dev/zero` bellek doldurur. Unix'te
`resource.setrlimit` bunu process seviyesinde kısıtlar; Windows
için ayrı iş (026.2 Job Objects).

## İhtiyaç (tek cümle)
`ATLAS_SANDBOX_CPU_S` + `ATLAS_SANDBOX_MEM_MB` env verildiğinde,
Unix'te shell subprocess'i `preexec_fn` içinde `RLIMIT_CPU` ve
`RLIMIT_AS` ile kısıtlansın; Windows'ta sessiz no-op (026.2'ye
kadar).

## Ölçülebilir Başarı
- **M1 — Env sözleşmesi:**
  - `ATLAS_SANDBOX_CPU_S` — CPU saniyesi (int). Yoksa kısıt yok.
  - `ATLAS_SANDBOX_MEM_MB` — address space (MB, int). Yoksa yok.
- **M2 — Unix uygulama:** shell subprocess `preexec_fn=` alır,
  `resource.setrlimit(RLIMIT_CPU, (n, n))` ve/veya
  `resource.setrlimit(RLIMIT_AS, (n*1024*1024, n*1024*1024))`.
- **M3 — Fork bomb / CPU testi (Unix):** `ATLAS_SANDBOX_CPU_S=1` +
  `python -c "while True: pass"` → SIGXCPU → exit != 0 (SIGKILL/9
  ya da 137/-9). Test 3 sn'den kısa sürer.
- **M4 — OOM testi (Unix):** `ATLAS_SANDBOX_MEM_MB=32` + `python -c
  "x = 'x' * 200_000_000"` → MemoryError → exit != 0.
- **M5 — Windows sessiz no-op:** env verildi ama `preexec_fn`
  ATANMADI, subprocess çalıştı. Uyarı basılmaz (spam engeli).
- **M6 — Env parse hata → yoksay:** `ATLAS_SANDBOX_CPU_S=abc` →
  kısıt yok, subprocess normal çalışır.
- **M7 — Env yok → bit-uyumlu:** hiçbir kısıt env'i verilmezse
  `preexec_fn=None`, mevcut 026 davranışı.
- **M8 — Test:** Unix canlı (`@pytest.mark.skipif(sys.platform ==
  "win32")`); Windows canlı no-op kabul; ortak env parse
  yardımcıları her platformda.
- **M9 — DECISIONS:** [KARAR] `resource` Windows'ta yok →
  `try: import resource` platform dallanması; `preexec_fn` Windows
  subprocess.run'da ValueError verir → None geç.

## Kapsam DIŞI
- Windows Job Objects — 026.2 kapsamı.
- RLIMIT_NPROC (process sayısı) — Docker olmadan fork bomb'u
  RLIMIT_CPU zaten SIGXCPU ile kesiyor; ekstra karmaşa YAGNI.
- User namespace / seccomp / capabilities — Linux-specific, geniş
  scope, ayrı iş.
- Container/chroot — Docker YASAK (026 direktifi).
- Aynı sınır run/plan seviyesinde config — YAGNI, env global yeter.

## Kısıt
- `Action`, `make_action`, `ActionDeniedError` imzaları korunur.
- `_scrub_env`, `_read_sandbox_timeout` davranışı değişmez.
- Env yokken hiçbir davranış farkı yok (bit-uyumlu regresyon test).
- Türkçe hata mesajı.
- Windows CI leg (test-windows) 026.1 canlı testi skip'ler; Unix
  CI leg (quality) canlı test koşar.

# 026.4 — Ship

## Sonuç
- **Unix `RLIMIT_NPROC` uygulama:** `_build_preexec_fn` içine
  `setrlimit(RLIMIT_NPROC, (n, n))` çağrısı eklendi. Child process'in
  aktif process (fork) sayısı `n` ile sınırlıdır.
- **Env sözleşmesi tam simetrik:** `ATLAS_SANDBOX_MAX_PROC` artık
  hem Unix (026.4 RLIMIT_NPROC) hem Windows (026.2 Job
  ACTIVE_PROCESS). Kullanıcı sözleşmesi platform-agnostik oldu —
  matris **8/8 dolu**.
- **`getattr` platform koruma:** `getattr(_resource, "RLIMIT_NPROC",
  None)` — bazı BSD varyantlarında sabit farklı olabilir. Yoksa
  sessizce atlanır (env verilse dahi çağrı yapılmaz).
- **Env yoksa bit-uyumlu:** üç env de yoksa `_build_preexec_fn`
  None döner (026.1 davranışı).
- **Windows sessiz no-op:** MAX_PROC verilse dahi Windows'ta
  preexec_fn None (026.1 guard aynı); MAX_PROC Windows'ta 026.2
  Job Object yolu ile karşılanır.
- **Test:** +4 test (mock-based; canlı fork limit CI-fragile
  bilinçli dışlandı).

## Dosyalar
```
src/atlas_core/orchestrator/actions.py    (edit: _build_preexec_fn'e
                                            MAX_PROC parametresi +
                                            RLIMIT_NPROC getattr koruma;
                                            docstring 026.4 kaydı)
tests/test_actions_unix_resource.py       (edit: +4 test 026.4:
                                            Windows MAX_PROC yine None,
                                            Unix MAX_PROC callable,
                                            RLIMIT_NPROC yok sessiz
                                              (fake resource),
                                            setrlimit mock çağırır
                                              ((6, (12,12))) doğrulama)
pipeline/tasks/026-4-unix-nproc/*.md      (2 artefakt)
```

## Sözleşme değişmezliği
- `_build_preexec_fn` imzası KORUNDU; içi genişledi.
- `Action`, `make_action`, `ActionDeniedError` imzaları KORUNDU.
- Env yokken 026.1 + 026.3 davranışı bit-uyumlu.
- Windows'ta hiçbir davranış değişmedi.
- Yeni env DEĞİL — `ATLAS_SANDBOX_MAX_PROC` 026.2'den beri var,
  Unix ayağı artık dolu.

## Kalite kapıları
- pytest: **629 passed + 12 skipped** (628 → +1 Windows canlı; +3
  Unix-only skip 026.4)
- coverage: %91.31 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/026.4-unix-nproc` — 032 üstünde tek commit.

## Env sözleşmesi
Değişmedi (`ATLAS_SANDBOX_MAX_PROC` 026.2'den beri var; 026.4 Unix
ayağını doldurdu).

## Platform matrisi (026 + 026.1 + 026.2 + 026.3 + 026.4 birleşik)
| Platform | Env yok | CPU_S | MEM_MB | MAX_PROC |
|---|---|---|---|---|
| Unix | subprocess.run (bit-uyumlu) | RLIMIT_CPU (026.1) | RLIMIT_AS (026.1) | **RLIMIT_NPROC (026.4)** |
| Windows | subprocess.run (bit-uyumlu) | Job PROCESS_TIME (026.3) | Job PROCESS_MEMORY (026.2) | Job ACTIVE_PROCESS (026.2) |

Matris **8/8 dolu** — hiç boşluk yok.

## Neden şimdi (026.1'de dışlanmıştı)
- 026.1 DECISIONS: "RLIMIT_CPU zaten fork bomb'u SIGXCPU ile keser
  (torun süreçler de aynı CPU budget'ten çeker)".
- Ancak 026.2 Windows tarafında `ACTIVE_PROCESS` gerçekten dolduğu
  için env sözleşmesi asimetrik kaldı — Unix'te `MAX_PROC` sessizce
  yoksayılıyordu.
- 026.4 semantik simetriyi kurar. Uyumsuzluk = subtle bug — kullanıcı
  taşınabilir bir sözleşme bekler.
- Fork bomb koruması bir yol yerine iki yol olur (CPU + NPROC) —
  kalıp: derin savunma, tek sınıra bel bağlama.

## Canlı fork limit testi bilinçli dışlandı
CI ortamında (özellikle Actions runner) fork limit deterministik
değil — mevcut kullanıcı zaten low-ulimit'te olabilir; fork sayısı
işletim sistemi durumuna bağlı. Mock ile `_build_preexec_fn`'in
gerçekten `setrlimit(RLIMIT_NPROC, ...)` çağırdığı ampirik
doğrulanır (calls == [(6, (12, 12))]).

## Kullanım örneği
```bash
# Unix'te fork bomb koruması:
$ ATLAS_SANDBOX_CPU_S=5 ATLAS_SANDBOX_MEM_MB=256 ATLAS_SANDBOX_MAX_PROC=16 \
    atlas run --goal-file build.yaml
# CPU 5 sn üstü SIGXCPU; 256 MB üstü SIGKILL; 16 fork üstü EAGAIN.

# Windows'ta aynı komut (bit-uyumlu env):
> set ATLAS_SANDBOX_CPU_S=5
> set ATLAS_SANDBOX_MEM_MB=256
> set ATLAS_SANDBOX_MAX_PROC=16
> atlas run --goal-file build.yaml
# CPU 5 sn üstü Job kill; 256 MB üstü Job kill; 16 process üstü Job cap.
```

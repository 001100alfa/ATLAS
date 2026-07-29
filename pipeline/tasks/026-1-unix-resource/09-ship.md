# 026.1 — Ship

## Sonuç
- **Unix uygulama:** shell subprocess `preexec_fn=` alır ve
  `resource.setrlimit(RLIMIT_CPU, (n, n))` + `resource.setrlimit(
  RLIMIT_AS, (n_MB*1024*1024,)*2)` uygular. Fork edilmiş child'da
  çalışır — parent etkilenmez.
- **Env sözleşmesi:**
  - `ATLAS_SANDBOX_CPU_S` — CPU saniye limiti (pozitif int).
  - `ATLAS_SANDBOX_MEM_MB` — address space (MB, pozitif int).
  - Her iki env de yoksa `preexec_fn=None` (mevcut 026 davranışı).
- **Windows sessiz no-op:** `_resource is None` VEYA `sys.platform
  == "win32"` → `_build_preexec_fn()` HER ZAMAN `None`. Windows
  `subprocess.run(preexec_fn=X)` ValueError verir; guard bunu önler.
- **Fail-safe:** env parse hatası (`abc`, `-1`, `0`, boş) → `None`
  (yoksay). Bit-uyumlu 026.
- **Kanıt (Windows canlı):** env verilse de subprocess normal
  çalışır (`test_0261_windows_shell_calisir_env_verili` → `exit=0
  out=ok`).
- **Kanıt (Unix canlı, CI Ubuntu leg):** `test_0261_unix_cpu_limit_sigxcpu`
  `while True: pass` 1 sn'de SIGXCPU alır (3.5 sn'den kısa); `test_0261
  _unix_mem_limit_memerror` 500 MB `bytearray` MEM_MB=64 iken exit != 0.

## Dosyalar
```
src/atlas_core/orchestrator/actions.py    (edit: +_resource import
                                            guard, +_read_positive_int_env,
                                            +_build_preexec_fn platform-aware,
                                            _shell'e preexec_fn=... geçir)
tests/test_actions_unix_resource.py       (yeni, +15 test:
                                            6 env parse, 2 Windows canlı,
                                            3 Unix _build_preexec_fn,
                                            3 Unix canlı [CPU/MEM/bit-uyumlu],
                                            1 _resource=None guard)
pipeline/tasks/026-1-unix-resource/*.md   (2 artefakt)
```

## Sözleşme değişmezliği
- `Action`, `make_action`, `ActionDeniedError` imzaları KORUNDU.
- `_scrub_env`, `_read_sandbox_timeout` davranışı DEĞİŞMEDİ.
- Env yokken subprocess.run çağrısı 026 ile bit-uyumlu
  (`preexec_fn=None` = varsayılan).
- Windows davranışı 026 ile birebir aynı — güvence garantili.

## Kalite kapıları
- pytest: **583 passed + 6 skipped** (574 → +9 canlı Windows; 6
  Unix-only skip → CI Ubuntu leg'de aktif)
- coverage: %91.34 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/026.1-unix-resource` — 018.2 üstünde tek commit.

## Env sözleşmesi (yeni ★)
| Değişken | Anlam |
|---|---|
| `ATLAS_SANDBOX_CPU_S` ★ | **026.1** — Unix RLIMIT_CPU (saniye) |
| `ATLAS_SANDBOX_MEM_MB` ★ | **026.1** — Unix RLIMIT_AS (MB); 026.2 Windows Job Objects'te de aynı ad |

## Platform matrisi
| Platform | Env yok | CPU_S=1 | MEM_MB=64 |
|---|---|---|---|
| Unix | preexec_fn None (bit-uyumlu 026) | fork bomb SIGXCPU'da ölür | 500MB alloc MemoryError |
| Windows | preexec_fn None | preexec_fn HÂLÂ None (sessiz no-op — 026.2'ye kadar) | preexec_fn HÂLÂ None |

## Not
026.2 Windows Job Objects aynı env adlarını (`ATLAS_SANDBOX_MEM_MB`)
paylaşır — kod yolu ayrı ama kullanıcı sözleşmesi platform-agnostik.
`ATLAS_SANDBOX_CPU_S` Windows'ta job objects ile birebir eşleştirilmez
(Windows CPU quota `JOB_OBJECT_LIMIT_PROCESS_TIME` = 100ns ticks) —
026.2 tasarımında ele alınır.

## Kullanım örneği
```bash
# Unix'te fork bomb koruması:
$ ATLAS_SANDBOX_CPU_S=5 ATLAS_SANDBOX_MEM_MB=256 \
    atlas run --goal-file build.yaml
# shell:make build 5 CPU sn geçemez, 256 MB'yi aşamaz.

# Windows'ta aynı komut çalışır ama Unix limitleri uygulanmaz
# (026.2 gelene kadar). Uyarı basılmaz — sessiz no-op tercihen.
```

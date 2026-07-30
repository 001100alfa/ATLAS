# 026.3 — Ship

## Sonuç
- **Windows CPU quota:** `JOB_OBJECT_LIMIT_PROCESS_TIME` (0x2) flag +
  `BasicLimitInformation.PerProcessUserTimeLimit` = `cpu_s *
  10_000_000` (100-nanosaniye tick). Subprocess CPU süresi
  aşıldığında **Windows kernel** tarafından kill.
- **Env sözleşmesi:** `ATLAS_SANDBOX_CPU_S` artık **hem Unix hem
  Windows'ta anlamlı** — 026.1 Unix'te RLIMIT_CPU, 026.3 Windows'ta
  Job Objects PROCESS_TIME. Kullanıcı sözleşmesi platform-agnostik.
- **`_apply_windows_job` imza:** `cpu_s: int | None = None`
  parametresi eklendi (varsayılan None, geri uyumlu).
- **`_has_windows_sandbox_env`:** CPU_S dahil üç env'den herhangi
  biri verilirse Windows Popen yolu tetiklenir.
- **`_shell` dispatch:** CPU_S env'den okunur, `_apply_windows_job`'a
  paralel MEM_MB + MAX_PROC + CPU_S üçlüsü olarak geçer.
- **Struct değişmedi** — `PerProcessUserTimeLimit` zaten
  `_JOBOBJECT_BASIC_LIMIT_INFORMATION` içinde `c_int64` olarak vardı.
  Yalnız flag + atama.
- **Kanıt (Windows canlı):** `test_0263_windows_cpu_quota_kesir`
  `while True: pass` sonsuz döngüsünü CPU_S=1 iken **3.5 sn'den kısa
  sürede** exit != 0 ile keser (timeout 8 sn olsa bile). CPU quota
  gerçekten çalışıyor.
- **Kanıt (Windows canlı, altında):** `test_0263_windows_cpu_s_altinda
  _kucuk_i_calisir` CPU_S=5 iken `print(1+1)` exit=0, çıktı `2`.

## Dosyalar
```
src/atlas_core/orchestrator/actions.py    (edit: +_JOB_OBJECT_LIMIT_PROCESS_TIME,
                                            +_WIN_TIME_TICKS_PER_SECOND;
                                            _has_windows_sandbox_env
                                              CPU_S dahil;
                                            _apply_windows_job cpu_s
                                              parametresi + flag +
                                              PerProcessUserTimeLimit
                                              atama;
                                            _shell CPU_S okuma + geçirme)
tests/test_actions_windows_job.py         (edit: +5 test 026.3:
                                            env CPU_S detection, apply
                                            erken çıkış üç None, Windows
                                            canlı CPU quota kesir,
                                            Windows CPU_S altında çalışır,
                                            non-Windows CPU_S run yolu)
pipeline/tasks/026-3-windows-cpu-quota/*.md  (2 artefakt)
```

## Sözleşme değişmezliği
- `Action`, `make_action`, `ActionDeniedError` imzaları KORUNDU.
- Env yokken `subprocess.run` yolu 026 ile bit-uyumlu.
- MEM_MB veya MAX_PROC verildi ama CPU_S yok → 026.2 davranışı
  birebir (yeni flag eklenmez).
- `_apply_windows_job` `cpu_s` default None → mevcut çağrıcılar
  değişmeden çalışır (imza genişledi ama geri uyumlu).
- Struct `_JOBOBJECT_EXTENDED_LIMIT_INFORMATION` layout DEĞİŞMEDİ.

## Kalite kapıları
- pytest: **610 passed + 9 skipped** (606 → +4 net; +5 canlı Windows,
  +1 non-Windows skip; 9 toplam skip = 6 Unix-only 026.1 + 2 non-Win
  026.2 + 1 non-Win 026.3)
- coverage: %91.26 (eşik %90)
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/026.3-windows-cpu-quota` — 018.3 üstünde tek commit.

## Env sözleşmesi
Değişmedi (env adı `ATLAS_SANDBOX_CPU_S` 026.1'den beri var).

## Platform matrisi (026 + 026.1 + 026.2 + 026.3 birleşik)
| Platform | Env yok | CPU_S | MEM_MB | MAX_PROC |
|---|---|---|---|---|
| Unix | subprocess.run (bit-uyumlu) | RLIMIT_CPU (026.1) | RLIMIT_AS (026.1) | — |
| Windows | subprocess.run (bit-uyumlu) | **Job PROCESS_TIME (026.3)** | Job PROCESS_MEMORY (026.2) | Job ACTIVE_PROCESS (026.2) |

Artık matrisin **her hücresi dolu** (Unix MAX_PROC hariç — RLIMIT_NPROC
026.1'de bilerek ele alınmadı, RLIMIT_CPU zaten fork bomb'u SIGXCPU
ile keser).

## 100ns tick hesabı
Windows API `LARGE_INTEGER` alanları (`PerProcessUserTimeLimit`) genelde
100-nanosaniye tick biriminde tanımlıdır — bu bir NT tarih/saat sözleşmesi
(FILETIME ile aynı birim).
- 1 saniye = 10⁷ tick
- Sabit: `_WIN_TIME_TICKS_PER_SECOND = 10_000_000`
- Overflow riski: `c_int64` max ≈ 9.2×10¹⁸; 10⁷ tick/s ile ≈ 29 000 yıl.
  Kullanıcı normal aralıklarda (1-3600 sn) taşma imkansız.

## Kullanım örneği
```powershell
# Windows'ta CPU quota koruması:
> set ATLAS_SANDBOX_CPU_S=5
> set ATLAS_SANDBOX_MEM_MB=256
> atlas run --goal-file build.yaml
# shell:cmd /c build.bat 5 CPU sn geçemez, 256 MB'yi aşamaz.

# Unix'te aynı komut → 026.1 RLIMIT_CPU + RLIMIT_AS
$ ATLAS_SANDBOX_CPU_S=5 ATLAS_SANDBOX_MEM_MB=256 atlas run ...
```

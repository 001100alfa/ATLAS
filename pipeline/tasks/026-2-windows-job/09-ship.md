# 026.2 — Ship

## Sonuç
- **Windows Job Objects uygulama:** `_apply_windows_job(pid, mem_mb,
  max_proc)` kernel32 üstünden:
  1. `CreateJobObjectW(None, None)` → HANDLE
  2. `SetInformationJobObject(handle, 9, EXTENDED_LIMIT_INFO)`
     (JobObjectExtendedLimitInformation)
  3. `OpenProcess(SET_QUOTA|TERMINATE, False, pid)`
  4. `AssignProcessToJobObject(job, proc_handle)`
- **KILL_ON_JOB_CLOSE (0x2000)** her koşulda flags'e eklenir —
  parent (ATLAS) kapanınca job da ölür, fork bomb torunları
  temizlenir.
- **Env sözleşmesi:**
  - `ATLAS_SANDBOX_MEM_MB` (026.1 ile ORTAK; pozitif int, MB) →
    `JOB_OBJECT_LIMIT_PROCESS_MEMORY` (0x100).
  - `ATLAS_SANDBOX_MAX_PROC` (yeni; pozitif int) →
    `JOB_OBJECT_LIMIT_ACTIVE_PROCESS` (0x8).
  - Her ikisi de yoksa Windows subprocess **eski `subprocess.run`
    yoluyla** çalışır (bit-uyumlu 026 + 026.1).
- **Timing:** Env varsa `subprocess.Popen` yolu kullanılır (pid al
  → Job'a ata → `communicate`). Env yoksa mevcut `subprocess.run`
  (bit-uyumlu).
- **Non-Windows sessiz no-op:** `sys.platform != "win32"` →
  `_apply_windows_job` erken çıkış False; `_has_windows_sandbox_env
  is True` olsa dahi Popen yoluna girilmez.
- **Fail-safe:** ctypes çağrılarından herhangi biri başarısız →
  stderr uyarı (`WinError <kod>`), subprocess kısıtsız yürür,
  planner turu ölmez.
- **Kanıt (Windows canlı):**
  - `test_0262_windows_mem_limit_patlar` — MEM_MB=64 iken
    `bytearray(500 * 1024 * 1024)` 8 sn'den kısa sürede exit != 0.
  - `test_0262_windows_mem_limit_altinda_calisir` — MEM_MB=256 +
    küçük alloc → exit=0 (kısıt altında normal).
  - `test_0262_windows_env_yok_bit_uyumlu` — env yok → mevcut
    `subprocess.run` yolu, 026 davranışıyla eş.
- **Kanıt (Windows canlı fail-safe):** `test_0262_windows_invalid_pid_uyari`
  — 0xFFFFFFFE gibi var olmayan pid → OpenProcess başarısız →
  stderr'de "026.2 OpenProcess... başarısız (WinError ...)".

## Dosyalar
```
src/atlas_core/orchestrator/actions.py    (edit: +_JOB_* sabitleri,
                                            +_has_windows_sandbox_env,
                                            +_apply_windows_job (ctypes
                                              wrapper, kernel32 çağrıları,
                                              WinDLL + wintypes structs),
                                            _shell'de Windows+env → Popen +
                                              apply_job + communicate;
                                              Unix ve env yok → mevcut
                                              subprocess.run yolu)
tests/test_actions_windows_job.py         (yeni, +11 test:
                                            2 non-Windows dispatch no-op,
                                            4 env detection,
                                            1 Windows bit-uyumlu,
                                            2 Windows MEM canlı (patlar/altında),
                                            1 apply erken-çıkış,
                                            1 Windows invalid pid fail-safe)
pipeline/tasks/026-2-windows-job/*.md     (2 artefakt)
```

## Sözleşme değişmezliği
- `Action`, `make_action`, `ActionDeniedError` imzaları KORUNDU.
- 026 + 026.1 davranışları env yokken bit-uyumlu — `subprocess.run`
  yolu değişmedi.
- Non-Windows: env verilse dahi Job Objects yolu YOK — hiçbir
  ctypes syscall'ı ateşlenmez.
- CtType kullanımı: yalnız stdlib (`ctypes` + `ctypes.wintypes`) —
  ek bağımlılık YOK.

## Kalite kapıları
- pytest: **592 passed + 8 skipped** (583 → +9 canlı Windows; 8 total
  skip = 6 Unix-only 026.1 + 2 non-Windows-only 026.2)
- coverage: %90.87 (eşik %90)
- mypy strict + ruff: temiz (N801 CapWords Windows SDK struct
  isimleri için `# noqa: N801` bilinçli)
- atlas scan: sır bulunamadı

## Branch
`feat/026.2-windows-job` — 026.1 üstünde tek commit.

## Env sözleşmesi (yeni ★)
| Değişken | Anlam |
|---|---|
| `ATLAS_SANDBOX_MEM_MB` ★ | **026.1 + 026.2 ORTAK** — Unix RLIMIT_AS / Windows JOB_OBJECT_LIMIT_PROCESS_MEMORY (MB) |
| `ATLAS_SANDBOX_MAX_PROC` ★ | **026.2** — Windows JOB_OBJECT_LIMIT_ACTIVE_PROCESS (aktif process sayısı) |

## Platform matrisi (026 + 026.1 + 026.2 birleşik)
| Platform | Env yok | CPU_S | MEM_MB | MAX_PROC |
|---|---|---|---|---|
| Unix | subprocess.run (bit-uyumlu) | RLIMIT_CPU | RLIMIT_AS | (026.2 kapsamı, ele alınmadı) |
| Windows | subprocess.run (bit-uyumlu) | (ele alınmadı — 026.3?) | JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_ACTIVE_PROCESS |

## Kullanım örneği
```bash
# Windows'ta OOM + fork bomb koruması:
> set ATLAS_SANDBOX_MEM_MB=256
> set ATLAS_SANDBOX_MAX_PROC=8
> atlas run --goal-file build.yaml
# shell:cmd /c build.bat 256 MB'yi aşamaz, 8 process'ten fazla açamaz.
# ATLAS kapanırsa job da ölür — arta kalan çocuk süreç YOK.

# Unix'te aynı env:
$ ATLAS_SANDBOX_MEM_MB=256 atlas run ...
# 026.1 RLIMIT_AS uygulanır (MAX_PROC yoksayılır Unix'te — 026.2 kapsamı Windows).
```

## Struct offset doğrulaması
`JOBOBJECT_EXTENDED_LIMIT_INFORMATION` layout ctypes tarafından
otomatik hesaplanır (`_fields_` sırası + alignment). 64-bit
Windows'ta beklenen offset'ler:
- `BasicLimitInformation`: 0
- `IoInfo`: 48 (basic sonrası, alignment ile)
- `ProcessMemoryLimit`: ~112
- `JobMemoryLimit`: ~120

Test canlı doğrulama (`test_0262_windows_mem_limit_patlar`) offset
hatası olsaydı MEM limitini uygulayamaz, subprocess başarılı
biterdi — geçen test = struct doğru.

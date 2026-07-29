# 026.2 — İhtiyaç: Windows Job Objects

## Bağlam
026.1 Unix'te fork bomb / OOM'a `resource.setrlimit` ile kısıt
getirdi ama Windows'ta boşta kaldı — sessiz no-op olarak duruyor.
Windows'ta process seviyesinde kısıt için native mekanizma: **Job
Objects**. Bir process'i job'a ata + `SetInformationJobObject` ile
memory/process limit ver; `KILL_ON_JOB_CLOSE` ile parent kapanınca
child'lar da ölür (fork bomb'un torunları dahil).

## İhtiyaç (tek cümle)
Windows'ta shell subprocess başlatılınca, `ATLAS_SANDBOX_MEM_MB` ve
`ATLAS_SANDBOX_MAX_PROC` env'leri verildiyse, kernel32 Job Objects
üstünden memory + active-process kısıtı uygulansın.

## Ölçülebilir Başarı
- **M1 — Env sözleşmesi:**
  - `ATLAS_SANDBOX_MEM_MB` (026.1 ile ORTAK; pozitif int, MB) →
    `JOB_OBJECT_LIMIT_PROCESS_MEMORY`.
  - `ATLAS_SANDBOX_MAX_PROC` (yeni; pozitif int) →
    `JOB_OBJECT_LIMIT_ACTIVE_PROCESS`.
  - Her ikisi de yoksa Job Objects mekanizması hiç kurulmaz
    (varsayılan davranış, ekstra syscall yok).
- **M2 — ctypes sarmalayıcı:** `_apply_windows_job(pid, mem_mb,
  max_proc)`:
  - `CreateJobObjectW(None, None)` → HANDLE.
  - `SetInformationJobObject(handle, 9, EXTENDED_LIMIT_INFO)` —
    `JobObjectExtendedLimitInformation` (=9). Struct `JOBOBJECT_EXTENDED
    _LIMIT_INFORMATION` (144 byte 64-bit).
  - `LimitFlags |= JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (0x2000) —
    ATLAS kapanırsa job da ölür (fork bomb temizlik).
  - `mem_mb` verildiyse `PROCESS_MEMORY_LIMIT` (0x100) + `ProcessMemoryLimit`.
  - `max_proc` verildiyse `ACTIVE_PROCESS` (0x8) + `ActiveProcessLimit`.
  - `OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid)` →
    `AssignProcessToJobObject(job, process_handle)`.
  - Her adım `GetLastError()` denetimi → hata log.
- **M3 — Non-Windows sessiz no-op:** `sys.platform != "win32"` →
  `_apply_windows_job` fonksiyonu ÇAĞRILMAZ (dispatch).
- **M4 — Timing:** Job Object subprocess **başladıktan sonra** atanır
  — subprocess.Popen ile pid alınır, Job'a atanır, sonra process
  serbest bırakılır. `subprocess.run` yerine `Popen` + `communicate`
  kullanılır (Windows kısıt aktifken); Unix ve env yoksa mevcut
  `subprocess.run` yolu korunur (bit-uyumlu regresyon test).
- **M5 — Windows canlı MEM kanıtı:** `ATLAS_SANDBOX_MEM_MB=64` +
  `python -c "bytearray(500*1024*1024)"` → subprocess killed (exit
  != 0) 8 sn'den kısa.
- **M6 — Windows canlı PROC kanıtı:** `ATLAS_SANDBOX_MAX_PROC=1` +
  komut spawn eden bir child → ikinci spawn başarısız (Access
  Denied ya da child ölür).
- **M7 — Env parse hatası → yoksay** (026.1 kalıbı, `_read_positive_
  int_env` ortak).
- **M8 — Non-Windows env verili → yoksay** (`_apply_windows_job`
  hiç çağrılmaz).
- **M9 — Fail-safe:** ctypes çağrısı başarısız (HANDLE None, WinError
  != 0) → stderr uyarı, subprocess normal yürür (kısıt YOK ama iş
  durmaz). Kritik hata mesajı `GetLastError` kodunu içerir.
- **M10 — Test:** Windows canlı MEM + PROC (skipif non-Windows); non-
  Windows kolunda dispatch no-op; env parse ortak (026.1 ile).
- **M11 — DECISIONS:** [KARAR] Job Objects neden `resource` yerine
  Windows tercihi (native kernel mekanizması, admin yetkisi gerekmez,
  fork bomb torunlarını yakalar); struct offset'lerini nasıl bulduk
  (Windows API doc + ampirik ölçüm).

## Kapsam DIŞI
- CPU quota (`JOB_OBJECT_LIMIT_PROCESS_TIME`) — Windows ns tick
  matematiği hassas, ayrı iş (026.3 belki). Bugünkü kapsam MEM +
  PROC — fork bomb + OOM iki büyük risk.
- Job Object nested (job içinde job) — Windows 8+'da var ama
  kompleks. YAGNI.
- UI-kısıt (job restrictions) — masaüstü etkileşimi olmayan
  subprocess, gerek yok.
- Access token restrictions — Docker YASAK direktifi altında;
  process-level yeter.

## Kısıt
- `Action`, `make_action`, `ActionDeniedError` imzaları korunur.
- Env yokken `subprocess.run` yolu korunur (bit-uyumlu 026 + 026.1).
- Env verildi ama non-Windows → env sessizce yoksayılır (uyarı yok —
  026.1 kalıbı, spam engeli).
- Ctypes: yalnız stdlib (`ctypes`, `ctypes.wintypes`).
- Türkçe uyarı.

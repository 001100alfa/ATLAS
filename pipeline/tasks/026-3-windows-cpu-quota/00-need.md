# 026.3 — İhtiyaç: Windows CPU quota (Job Objects PROCESS_TIME)

## Bağlam
Platform matrisinde tek boşluk: Windows'ta `ATLAS_SANDBOX_CPU_S`
kullanılmıyor (026.2 sadece MEM + PROC ele almıştı). Unix'te
`RLIMIT_CPU` çalışıyor, ama fork bomb / sonsuz döngü Windows'ta
yalnız timeout ile kesiliyor (10 sn varsayılan) — daha keskin
bir sınır yok.

## İhtiyaç (tek cümle)
`ATLAS_SANDBOX_CPU_S` env Windows'ta da anlamlı olsun:
`JOB_OBJECT_LIMIT_PROCESS_TIME` (0x2) + `BasicLimitInformation.
PerProcessUserTimeLimit` (100ns tick = `cpu_s * 10_000_000`) ile
subprocess CPU süresi bittiğinde kill.

## Ölçülebilir Başarı
- **M1 — Env sözleşmesi:** `ATLAS_SANDBOX_CPU_S` **kümülatif ortak**
  (026.1 Unix + 026.3 Windows). Değer birimi saniye (pozitif int).
  Yoksa Windows'ta CPU quota UYGULANMAZ (bit-uyumlu 026.2).
- **M2 — Windows Job flag:** `LimitFlags` bit değeri **0x2** eklenir
  ve struct'ın `BasicLimitInformation.PerProcessUserTimeLimit`
  alanına `cpu_s * 10_000_000` (100ns tick) yazılır.
- **M3 — `_apply_windows_job` imza güncellemesi:** `cpu_s: int | None`
  parametresi eklenir. Yoksa flag ateşlenmez (bit-uyumlu).
- **M4 — `_has_windows_sandbox_env` `CPU_S` dahil:** üç env'den
  herhangi biri verilirse Windows Popen yolu tetiklenir.
- **M5 — `_shell` dispatch:** CPU_S'i env'den okuyup `_apply_windows_job`'a
  geçirir (mem_mb / max_proc / cpu_s üçü paralel).
- **M6 — Windows canlı kanıt:** `ATLAS_SANDBOX_CPU_S=1` +
  `python -c "while True: pass"` → subprocess kill, exit != 0, 3.5
  sn'den kısa (timeout 8 sn olsa bile CPU quota keser).
- **M7 — Non-Windows sessiz no-op:** `_apply_windows_job` non-Windows'ta
  hiç çağrılmaz (mevcut guard); Unix'te CPU_S 026.1 RLIMIT_CPU yolu
  ile ele alınır (kod yolu ayrı).
- **M8 — Env parse hatası → yoksay:** `abc`/negatif/0 → CPU quota
  uygulanmaz (026.1 fail-safe kalıbı).
- **M9 — Test:** +4 test — env detection CPU_S dahil, Windows canlı
  CPU quota kill, Windows bit-uyumlu env yok, apply erken-çıkış
  (mem/proc/cpu üçü de None).
- **M10 — DECISIONS:** [KARAR] 100ns tick çevirme; neden PerProcess vs
  PerJob (PerJob tüm job için toplam; PerProcess her child için ayrı
  — subprocess'in kendisi + torunları toplam limitle yaşar → doğru
  seçim); mevcut struct alanı `PerProcessUserTimeLimit` zaten `c_int64`
  olarak tanımlıydı, sadece flag + değer atama.

## Kapsam DIŞI
- Wall-clock CPU limit (kernel time dahil) — user time yeter,
  sanal makine hıçkırıklarını kesme.
- Per-job CPU budget (`PerJobUserTimeLimit`) — tek subprocess için
  YAGNI; batch paralel (031) düşünülürse ele alınabilir.
- Windows CPU quota Unix ile birebir eşleşme (SIGXCPU semantiği vs
  Windows kill) — exit kodu semantiği farklı, sözleşme "subprocess
  bitirilir" yeter.

## Kısıt
- `_apply_windows_job` mevcut çağrıcıları (yalnız `_shell` içi tek yer)
  güncellenir; imza yeni parametreye genişler.
- `_has_windows_sandbox_env` mevcut kullanıcıları etkilenmez (yalnız
  `_shell` içi).
- Env yokken kod yolu bit-uyumlu 026.2 + 026.1.
- Struct değişmedi — `PerProcessUserTimeLimit` zaten `c_int64`.
- Türkçe uyarı + docstring.

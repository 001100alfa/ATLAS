# Görev 180 — İhtiyaç

SPEC 170 `ai-cli status --alert-webhook` payload'ında `up_to_date=False`
bilgisi var ama paketin BOYUTU + WEBHOOK ZAMANI yok — monitoring
alıcısı "büyük drift" ve "kaç dakikadır düşük" farkını payload'dan
göremez.

## Kabul

- SPEC 170 payload'a **iki yeni alan** (SPEC 032.4 bit-uyumlu):
  - `size_bytes`: int (SPEC 037.4 `size_bytes` alanı; payload'a taşı)
  - `timestamp`: str (ISO 8601 seconds; `_dt.now().isoformat(timespec="seconds")`)
- Değerler: `size_bytes` = mevcut `report["size_bytes"]`;
  `timestamp` = `datetime.now().isoformat(timespec="seconds")`.
- Mevcut 5 alan (`alert`, `name`, `installed_version`,
  `declared_version`, `up_to_date`, `install_dir`) DOKUNULMADI.
- Test: SPEC 170 mevcut testleri kırmaz + yeni test `size_bytes` +
  `timestamp` payload'ı doğrular (ISO 8601 regex).
- SPEC 146 `--schema` kısa devre DOKUNULMADI (schema modu POST atmaz).
- SPEC 037.4 normal status davranışı AYNI.

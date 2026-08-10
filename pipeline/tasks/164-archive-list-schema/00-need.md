# Görev 164 — İhtiyaç

SPEC 149 `atlas archive --schema` çıktısı archive KOMUTUNUN geneli
için (top_level=record biçimi, exit_codes=tüm alt komutlar için).
Ancak `archive --list` ve `archive --restore`'un exit_codes'ları
farklı: --list yalnız 0/2 çıkarır; --restore ise 0/2/3/6 çıkarır.
Şu an bilgi tek yerde toplanmış — hangi alt komutun hangi exit code'u
çıkardığını schema kullanıcısı bilmiyor.

## Kabul

- `atlas archive --schema` JSON çıktısına `sub_commands` alanı ekle
  (SPEC 032.4 alan-ekleme bit-uyumlu):
  - `list`:    `{exit_codes: ["0","2"], spec: "075"}`
  - `restore`: `{exit_codes: ["0","2","3","6"], spec: "033"}`
  - `search`:  `{exit_codes: ["0","2"], spec: "065"}`
  - `all`:     `{exit_codes: ["0","2"], spec: "012"}`
- `atlas archive --list --schema` mevcut `archive --schema` ile
  BİREBİR AYNI çıktı verir (schema kısa devre --list öncesi).
- `sub_commands` alanı Prometheus çıktısına EKLENMEZ (YAGNI —
  yeni metric aile gerekir). Yalnız JSON.
- `--pretty --list --schema` indent=2 çalışır.
- Mevcut top_level/exit_codes/formats/notes DOKUNULMADI.
- SPEC 149/151/155 mevcut davranışları BİT-UYUMLU.

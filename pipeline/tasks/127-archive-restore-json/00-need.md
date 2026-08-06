# Görev 127 — İhtiyaç

SPEC 033 `atlas archive --restore <id>` dry-run insan-okunur çıktı basıyor.
CI/scripting için JSON çıktı gerek (SPEC 075/098 kalıbı: dry-run planı
JSON dict). Uygulama sonrası (--apply) da JSON gerekir.

## Kabul

- `atlas archive --restore <id> --json` (VEYA `--restore --search P --json`).
- Dry-run JSON: `{"mode":"dry-run","task_id","archive","target","conflict":bool}`.
- Apply JSON: `{"mode":"apply","task_id","archive","target","restored":true}`.
- Hata durumları JSON basmaz (stderr'e mevcut SPEC HATASI); rc mevcut
  değerleri korur (2/3/6).
- `--json` VERİLMEZSE SPEC 033/071 pretty AYNI.

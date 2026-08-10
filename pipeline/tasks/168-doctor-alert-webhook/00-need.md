# Görev 168 — İhtiyaç

SPEC 064 metrics --alert-webhook, SPEC 165 vault verify --alert-webhook
kalıbı doctor için de gerek — quality.* uyarısı varsa uzak alert.

## Kabul

- `atlas doctor --alert-webhook URL`.
- Bulgu ölçütü: `_has_quality_warning(report)` True (quality.* alt-
  dict'lerinden en az birinde `warning` alanı var).
- Bulgu YOKSA POST atılmaz (sessiz).
- POST payload (SPEC 064/165 kalıbı):
  ```json
  {
    "alert": "doctor",
    "warnings": ["<top-level warning satırı>", ...],
    "quality_warnings": {"<field>": "<message>", ...}
  }
  ```
- `_post_alert_webhook()` yeniden kullanılır.
- Başarısız POST → stderr uyarı; exit code KORUNUR (SPEC 064/165 kalıbı).
- --strict ile ORTOGONAL (webhook exit 9'u etkilemez).
- Yalnız ana `_cmd_doctor` sağlık raporu için — diff/history/ping alt
  dispatcher'larında SPEC 168 kapsam dışı (YAGNI; ileri SPEC'te).
- Parser: `--alert-webhook URL` yeni argüman.

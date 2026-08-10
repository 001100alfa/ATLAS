# Görev 170 — İhtiyaç

SPEC 064/165/168 kalıbı ai-cli status için: paket `up_to_date=False`
olduğunda uzak alert POST.

## Kabul

- `atlas ai-cli status <name> --alert-webhook URL`.
- Bulgu ölçütü: `up_to_date=False` (installed != declared_clean).
- `up_to_date=True` → POST atılmaz (sessiz).
- POST payload (SPEC 064/165/168 kalıbı):
  ```json
  {
    "alert": "ai-cli-status",
    "name": "<paket>",
    "installed_version": "<x.y.z|null>",
    "declared_version": "<^x.y.z>",
    "up_to_date": false,
    "install_dir": "<path>"
  }
  ```
- `_post_alert_webhook()` yeniden kullanılır.
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- Normal ai-cli status davranışı BİT-UYUMLU (--alert-webhook yoksa).
- SPEC 146 `--schema` kısa devre dispatcher önce; --alert-webhook
  YOK sayılır schema modunda (bilgi komutu değil).
- Parser: `--alert-webhook URL` yeni argüman.
- --json / --json-lines çıktısı --alert-webhook ile ortogonal
  (webhook POST'u stdout'a dokunmaz).

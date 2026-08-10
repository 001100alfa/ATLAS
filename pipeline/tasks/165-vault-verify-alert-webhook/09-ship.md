# Görev 165 — Teslim

`atlas vault verify --alert-webhook URL`.

## Uygulama
- `_cmd_vault_verify` sonunda `--strict` kontrolünden ÖNCE webhook POST
  (SPEC 064 metrics kalıbı).
- Bulgu ölçütü: `report.is_clean` False (broken_links + orphan_notes +
  orphan_tags herhangi biri boş değil).
- POST payload SPEC 064 kalıbı: `alert=vault-verify` + vault_root +
  notes/links/tags_total + broken_links/orphan_notes/orphan_tags sayıları.
- `_post_alert_webhook()` yeniden kullanıldı (dış bağımlılık YOK,
  stdlib urllib.request; SSRF savunma dahili).
- Başarısız POST → stderr uyarı; exit code KORUNUR.
- --strict ile ORTOGONAL (webhook exit 4'ü etkilemez).
- Parser: `--alert-webhook URL` yeni argüman; default None.

## Kanıt
- +6 test (`tests/test_cli_vault_verify_alert_webhook.py`) —
  ephemeral HTTP server ile POST doğrulama:
  1. Kırık link varsa POST atılır (200) + doğru payload alanları
  2. Temiz vault (is_clean True) → POST atılmaz (sessiz)
  3. POST 500 → başarısız stderr; exit code KORUR
  4. `--strict` ile birlikte: POST atılır + exit 4 (ortogonal)
  5. --alert-webhook YOK → SPEC 042 davranışı AYNI (bit-uyumlu)
  6. SSRF savunma: file:// scheme → POST başarısız
- vault_verify + vault_backup regresyon 174 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 042 normal vault verify çıktısı AYNI (--alert-webhook yoksa).
- SPEC 087/092/111/136/140/145 --format/--out/--gzip/--schema DOKUNULMADI.
- SPEC 064 `_post_alert_webhook()` implementasyonu AYNI (yeniden kullanıldı).
- --strict SPEC 042 exit 4 semantiği AYNI (webhook ortogonal).

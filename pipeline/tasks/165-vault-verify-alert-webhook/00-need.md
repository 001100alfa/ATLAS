# Görev 165 — İhtiyaç

SPEC 064 metrics --alert-webhook, SPEC 131/135 doctor --alert-webhook,
SPEC 141 atlas-ci-status.yml alert-webhook — hepsi belirli bir bulgu
durumunda URL'ye JSON POST atıyor. `vault verify` için bu eksik: kırık
link/orfan not/orfan tag bulunduğunda uzak alert yok.

## Kabul

- `atlas vault verify --alert-webhook URL`.
- Bulgu ölçütü: `report.is_clean` False (broken_links / orphan_notes /
  orphan_tags'den en az biri boş değil).
- Bulgu YOKSA POST atılmaz (sessiz).
- POST payload (SPEC 064 kalıbı):
  ```json
  {
    "alert": "vault-verify",
    "vault_root": "<path>",
    "notes_total": int, "links_total": int, "tags_total": int,
    "broken_links": int, "orphan_notes": int, "orphan_tags": int
  }
  ```
- Yardımcı fonksiyon `_post_alert_webhook()` YENİDEN KULLANILIR.
- Başarısız POST → stderr'e uyarı; exit code KORUNUR (SPEC 064 kalıbı).
- --alert-webhook DIŞINDA vault verify davranışı BİT-UYUMLU (SPEC 042/
  087/092/111/136/140/145 hepsi AYNI).
- Parser: `--alert-webhook URL` yeni; default None.
- --strict ile ORTOGONAL (webhook exit 4'ü etkilemez).

# Görev 061 — İhtiyaç

SPEC 042 `atlas vault verify --json` şu an bir dict yayımlıyor ama şeması yalnız
kod içinde (`VerifyReport.to_dict`). Dış tüketiciler (Grafana dashboard, CI
scriptleri, 3. parti alertmanager) alanların kararlı sözleşmesini `docs/`
altında JSON Schema olarak beklerler.

## Kabul kriteri

- `docs/api/vault-verify-schema.json` Draft-07 uyumlu.
- 7 zorunlu alan (`broken_links, orphan_notes, orphan_tags, notes_total,
  links_total, tags_total, is_clean`).
- `broken_links` her item `{from, to}` (JSON `"from"` literal — Python `frm`).
- `additionalProperties: false` → gelecekte alan ekleme = **major bump**.
- Sayaç alanlarında `minimum: 0`.

## Test

Şema dosyasının kendisi + canlı `to_dict()` çıktısı ile uyumluluk. Minimal
Draft-07 doğrulayıcı test içinde (dış bağımlılık yok).

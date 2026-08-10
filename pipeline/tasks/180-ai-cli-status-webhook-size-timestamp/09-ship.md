# Görev 180 — Teslim

`ai-cli status --alert-webhook` payload'a `size_bytes` + `timestamp`
(SPEC 032.4 bit-uyumlu; SPEC 170 üstüne).

## Uygulama
- SPEC 170 `ai_payload` dict'ine 2 yeni anahtar:
  - `size_bytes`: mevcut `size_bytes` local (SPEC 037.4).
  - `timestamp`: `datetime.now().isoformat(timespec="seconds")` (ISO 8601).
- Mevcut 6 alan (`alert`, `name`, `installed_version`, `declared_version`,
  `up_to_date`, `install_dir`) DOKUNULMADI.
- Toplam payload alanı: 6 → **8**.

## Kanıt
- +4 test (`tests/test_cli_ai_cli_status_webhook_size_timestamp.py`):
  1. `size_bytes` alanı int + doğru değer (>=4096, blob dahil)
  2. `timestamp` ISO 8601 seconds regex eşleşmesi
  3. Alan sayısı tam 8 (6 mevcut + 2 yeni)
  4. up_to_date=True → POST atılmaz (SPEC 170 bit-uyumlu)
- ai_cli_status regresyon 52 test yeşil.
- mypy + ruff + scan temiz.

## Değişmeyen sözleşme
- SPEC 037.4 normal status davranışı AYNI (--alert-webhook yoksa).
- SPEC 118/120 --json-lines --out --gzip DOKUNULMADI.
- SPEC 146 --schema kısa devre POST'a girmez.
- SPEC 150/156 --format prometheus DOKUNULMADI.
- SPEC 170 POST tetik ölçütü AYNI (`up_to_date=False`).

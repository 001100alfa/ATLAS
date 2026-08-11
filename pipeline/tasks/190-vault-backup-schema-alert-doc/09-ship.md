# Görev 190 — Teslim

`vault backup --schema` JSON'a `alert_options` (1) + `alert_payload` (6).

## Uygulama
- SPEC 175/181/188/189 kalıbı vault backup için.
- SPEC 178 6 phase (backup/prune/split/encrypt) belgele — `phase` alanı
  desc'inde 4 seçenek adı bulunur.
- Prometheus'a EKLENMEDİ (YAGNI).

## Kanıt
- +5 test; vault_backup_schema regresyon 30 yeşil.

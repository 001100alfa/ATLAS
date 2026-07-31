# Görev 041.1 — İhtiyaç

SPEC 041 (`atlas vault backup`) mevcut ama cron/scheduled kullanım için
iki eksiği var:

1. `--out` YOKken zaten `default_backup_path`'a yazıyor ama **explicit
   intent yok**: audit satırı düz `backup`. Zamanlanmış çalıştırmayı
   normal manuel backup'tan ayırt edemiyoruz.
2. **Retention yok**: her cron çalıştırması yeni tar üretiyor; disk
   şişer.

## Kabul kriteri

- `atlas vault backup --auto`
  - `--out` ile karşılıklı dışlayıcı → çakışırsa exit 2 SPEC HATASI.
  - `default_backup_path(archive_root)` kullanır (bit-uyumlu).
  - Audit satırı: `atlas-vault` / **`backup-auto`** / `<path>`.
- `atlas vault backup [--auto] --keep N` (N ≥ 1)
  - Backup yazıldıktan sonra `<archive_root>/vault-*.tar.gz` dosyaları
    mtime desc sıraya konur; ilk N tutulur, geri kalanı silinir.
  - Yalnızca `vault-*.tar.gz` desenine uyan dosyalara dokunur (SPEC 007
    task arşivleri veya README.txt korunur).
  - Her silme için audit satırı: `atlas-vault` / **`prune`** / `<path>`.
  - `--out` verilmişse retention YOK sayılır; stderr'e `UYARI` basılır.
  - `N < 1` → exit 2 SPEC HATASI.
  - Silme hatası (`OSError`) → exit 6 (SPEC 041 sınıfı).
- `archive_root` yoksa `prune_backups` sessizce boş liste döner (cron
  nazikliği — hata değil).
- Mevcut `atlas vault backup [--out]` **bit-uyumlu**.

## Riskli

- `--keep` semantiği yalnızca `archive_root` içindeki `vault-*.tar.gz`
  dosyalarına uygulanır. `--out foo/x.tar.gz --keep 5` çağrılırsa
  `foo/`'da retention yapmaz (patika belirsiz olurdu); onun yerine
  uyarı basar. Kullanıcının beklentisi buysa `--auto` kullanmalı.
- `datetime.now()` ile üretilen `default_backup_path` aynı dakika
  içinde iki kere çağrılırsa aynı yola yazar (üzerine yazma). Cron
  minimum periyot ≥ 1 dk kabul.

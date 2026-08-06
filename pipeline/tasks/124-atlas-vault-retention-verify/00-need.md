# Görev 124 — İhtiyaç

SPEC 107 atlas-vault.yml `--keep 7` retention komutta var ama gerçekten
uygulandığı workflow'da doğrulanmıyor. Yeni step: archive/'de N ≤ 7
`vault-*.tar.gz*` dosya sayısını kontrol et.

## Kabul

- `.github/workflows/atlas-vault.yml` yeni step: `Verify retention
  (--keep 7)`.
- Backup+split+verify+doctor'dan sonra çalışır.
- `find archive/ -name 'vault-*.tar.gz*' | wc -l` ≤ 7 kontrolü
  (parça dosyalarını da sayar).
- Aşarsa `::error::` + exit 1.
- has_vault=false ise atlar.
- Mevcut step'ler DOKUNULMADI.

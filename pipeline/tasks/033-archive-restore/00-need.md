# Görev 033 — İhtiyaç

`atlas archive <task> --apply` görevi arşive gönderiyor ve
`pipeline/tasks/<task>` dizinini siliyor. Kullanıcı yanlışlıkla bir
görevi arşivlediyse ya da geçmiş bir görevi tekrar açıp devam etmek
istiyorsa manuel:

```
tar -xzf archive/003-*.tar.gz -C pipeline/tasks/
```

Bunu tek komut wrap: `atlas archive --restore <id> [--apply]`.

## Kabul kriteri
- `--restore <id>` (dry-run) → plan basar, dosya yazmaz.
- `--restore <id> --apply` → `<archive_root>/<id>-*.tar.gz`'in en
  yeni sürümünü `<tasks_root>/<id>` altına açar.
- Hedef zaten varsa → exit 3 (SPEC 007 exit uzayına uyum).
- Arşiv yoksa → exit 6.
- Path traversal (`..`, mutlak yol, Windows kolon `:`) reddedilir; tar
  kökü `<id>` değilse reddedilir.
- Audit log: `atlas-archive`, `restore`, `<id>`.

## Riskli
- Tar üyelerinin arcname kontrolü kritik: kötücül tar `pipeline/tasks/`
  dışına yazabilir. Testlerde negatif senaryolar var.
- Python 3.14 `tarfile.extractall` default filter değişimi → biz
  `filter="data"` verdik (3.12+).

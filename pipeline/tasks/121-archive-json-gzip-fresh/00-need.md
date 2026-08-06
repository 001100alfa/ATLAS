# Görev 121 — İhtiyaç

SPEC 115 `archive --list --json --out PATH` + SPEC 108 `--gzip` var ama
`--json --out --gzip` üç bayrak birlikte kanıtlanmadı. Regresyon önleme
için salt-test tur (SPEC 116 kalıbı).

## Kabul

- Yeni `tests/test_cli_archive_full_chain.py`.
- SPEC 075+079+085+093+108+115 tam zincir tek test dosyasında.
- Kod DEĞİŞMEZ.

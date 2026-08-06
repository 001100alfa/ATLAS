# Görev 129 — İhtiyaç

SPEC 087+092+111 zinciri (vault verify --format json-lines + --out +
--gzip + --strict) tam birlikte regresyon test yok. Salt-test tur
(SPEC 121/122/123 kalıbı).

## Kabul

- Yeni `tests/test_cli_vault_verify_full_chain.py`.
- Kod DEĞİŞMEZ; jsonl + out + gzip + strict + dump-report zinciri.

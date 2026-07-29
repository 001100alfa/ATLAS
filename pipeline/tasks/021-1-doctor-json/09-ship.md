# 021.1 — Ship

## Sonuç
`atlas doctor --json` bayrağı eklendi. Çıktı tek satır JSON:

```json
{
  "backend": {"ATLAS_LLM": "anthropic", "ANTHROPIC_API_KEY": "sk-***abc", ...},
  "retry_pricing": {"ATLAS_LLM_RETRIES": "0", ...},
  "storage": {"ATLAS_VAULT": "vault", ...},
  "warnings": ["ANTHROPIC_API_KEY yok", ...]
}
```

Refactor: veri toplama (`_collect_doctor_report`) sunum'dan ayrıldı;
`--json` doğrudan `json.dumps` eder; `--json` yoksa insan-okunur
format 021 bit-uyumlu.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +typing.Any import;
                                            _collect_doctor_report yardımcı;
                                            _cmd_doctor --json dallanma;
                                            parser --json flag)
tests/test_cli_direct.py                  (+4 test — JSON parse,
                                            key mask, warnings dolu,
                                            insan format regresyon)
pipeline/tasks/021-1-doctor-json/*.md     (5 artefakt)
```

## Sözleşme değişmezliği
- `atlas doctor` (021) mevcut alt-komut korundu; `--json` yeni bayrak.
- API key maskeleme JSON'da da uygulanır (savunma bit-uyumlu).
- Exit 0 (021 kalıbı).

## Kalite kapıları
- pytest: **494 passed** (490 → +4)
- mypy strict + ruff: temiz

## Branch
`feat/021.1-doctor-json` — 016.2 üstünde tek commit.

## Kullanım örneği
```bash
$ atlas doctor --json | jq '.warnings'
[
  "ANTHROPIC_API_KEY yok"
]

$ atlas doctor --json | jq -r '.backend.ATLAS_LLM'
anthropic
```

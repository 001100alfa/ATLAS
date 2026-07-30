# 032.5 — Ship

## Sonuç
- **`atlas doctor --json --pretty`** yeni bayrağı: girintili JSON
  (`json.dumps(indent=2, ensure_ascii=False)`).
- **Bit-uyumluluk:** `--pretty` yoksa mevcut tek satır davranışı
  BİREBİR. Mevcut CI tüketicileri değişmeden çalışır.
- **Bayrak birlikteliği:** `--pretty` `--json` olmadan sessizce
  yoksayılır (insan format zaten çok satırlı). `--strict + --pretty
  + drift` → exit 9 hala tetikler (bayrak yalnız biçim).

## Dosyalar
```
src/atlas_core/cli.py                     (edit: _cmd_doctor JSON
                                            yolunda indent=(2|None);
                                            parser --pretty)
tests/test_cli_doctor_strict.py           (+3 test 032.5)
pipeline/tasks/032-5-doctor-pretty/*.md   (2 artefakt)
```

## Kalite kapıları
- pytest: **683 passed + 12 skipped** (680 → +3)
- coverage: %91.18
- mypy strict + ruff: temiz
- atlas scan: sır bulunamadı

## Branch
`feat/032.5-doctor-pretty` — main üstünde tek commit.

## Kullanım
```bash
$ atlas doctor --json --pretty | less
{
  "schema_version": "1",
  "backend": { ... },
  ...
}

# CI hâlâ tek satır (varsayılan):
$ atlas doctor --json | jq '.quality.decisions_drift.drift_days'
0
```

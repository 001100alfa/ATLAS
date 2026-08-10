# Görev 184 — İhtiyaç

SPEC 132 `metrics --alert-history-show --json` NDJSON stream basar
ama `--format json-lines` seçeneği YOK — CLI tutarlılık (SPEC 087
vault verify, SPEC 166 doctor, SPEC 171 archive, SPEC 172 vault verify
schema hepsi `--format json-lines` kullanır). Kullanıcı `--json` vs
`--format json-lines` arasında hangisinin NDJSON olduğunu koddan
öğrenmek zorunda.

## Kabul

- `atlas metrics --alert-history-show --format json-lines
  [--out PATH]`.
- **Semantik**: `--format json-lines` = mevcut `--json` NDJSON stream
  ile BİT-UYUMLU (aynı `_json.dumps` per record + summary).
- `--json` ile `--format json-lines` MUTEX (aynı çıktı; iki bayrak
  aynı anda anlamsız) → SPEC HATASI exit 2.
- `--out PATH` desteklenir (SPEC 139 --json --out kalıbı).
- SPEC 143 `--format prometheus` DOKUNULMADI (mevcut dal).
- SPEC 132 human default (--format ve --json yoksa) AYNI.
- Parser: `--format` choices'a `json-lines` eklendi (mevcut sadece
  `prometheus` vardı).
- SPEC 148 --strict + exit 4 AYNI (--format json-lines dalında da).

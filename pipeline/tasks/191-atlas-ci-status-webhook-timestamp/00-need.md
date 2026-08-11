# Görev 191 — İhtiyaç

SPEC 185 kalıbı workflow-CLI parity: SPEC 141 `atlas-ci-status.yml`
webhook payload'ına `timestamp` (SPEC 180/186/187 CLI kardeşi).

## Kabul
- Payload heredoc'una `"timestamp":"$ts"` alan (ISO 8601 UTC).
- Değer: `ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)`.
- Mevcut 5 alan DOKUNULMADI.
- Step adı SPEC 191 referansı içerir.

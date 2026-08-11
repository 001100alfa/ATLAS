# Görev 191 — Teslim

`atlas-ci-status.yml` webhook payload'a `timestamp` (SPEC 185 kalıbı;
workflow-CLI parity SPEC 180/186/187 CLI kardeşleri).

## Uygulama
- SPEC 141 payload heredoc'una `"timestamp":"$ts"` alan.
- `ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)` ISO 8601 UTC.
- Mevcut 5 alan (alert/rc/run_id/sha/event) DOKUNULMADI.
- Step adı SPEC 191 referansı.

## Kanıt
- +3 test (SPEC 191); workflow test 128 yeşil.

## Kalıp not
Workflow-CLI parity — receiver aynı payload biçimini bekler (bash
date `-u` UTC = Python `datetime.now().isoformat()` local
timezone farkı monitoring için önemsiz — ikisi de ISO 8601 seconds).

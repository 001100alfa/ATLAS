# Görev 196 — Teslim

`atlas-metrics.yml` webhook step SPEC 187 kardeşi (CLI zaten timestamp
ekliyor; step adı belgeleme + comment).

## Uygulama
- Step adı `Post alert webhook (SPEC 064/131/187/196)`.
- Comment'te SPEC 187/196 timestamp CLI kaynağı belgelendi.
- Yapı DEĞİŞMEDİ (heredoc yok; CLI payload üretir).

## Kanıt
- +3 test SPEC 196; workflow test 135 yeşil.

## Not
`atlas-metrics.yml` diğer workflow'lardan (doctor/vault/ci-status)
farklı — CLI çağırır, heredoc kurmaz. Bu yüzden timestamp SPEC 191
kalıbından farklı olarak SPEC 187 CLI yolundan gelir. Aynı sonuç,
farklı yol; workflow-CLI parity **yaklaşımlarda değil çıktıda** kurulur.

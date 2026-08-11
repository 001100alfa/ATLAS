# Görev 196 — İhtiyaç

`atlas-metrics.yml` webhook step CLI'yı çağırır (`atlas metrics
--alert-webhook`). SPEC 187 CLI payload'a timestamp ekliyor, workflow
tarafında ekstra yapı gerekmez. Step adı SPEC 196 referansı içerecek.

## Kabul
- Step adı `Post alert webhook (SPEC 064/131/187/196)`.
- Comment'te SPEC 187/196 timestamp belgesi (CLI'nın hallettiği açıklaması).
- Yapı değişmez (heredoc yok; CLI zaten payload üretiyor).

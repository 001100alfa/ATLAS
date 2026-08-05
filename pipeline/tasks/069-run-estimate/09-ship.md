# Görev 069 — Teslim

`atlas run --estimate` — LLM çağırmadan cost öngörüsü.

## Uygulama

- `_estimate_run_cost(goal, backend, tokens_per_call, price_in, price_out)`
  yardımcı. Stub backend veya fiyat env yok → cost 0. Aksi: yarısı input
  yarısı output heuristik.
- `_cmd_run_goal`: en başta `--estimate` erken dallanma. Goal yüklenir,
  context+planner+sandbox HİÇ KURULMAZ. Sadece `_estimate_run_cost`
  sonucu insan/JSON basılır, exit 0. Audit dokunulmaz.
- Parser: `--estimate` (store_true) + `--json` (existing? yeni). Batch
  dispatcher (`_cmd_run`) tek dosya path'inde `estimate` + `json`
  değerlerini `_cmd_run_goal`'a iletir.

## Kanıt

- +11 test (`tests/test_cli_run_estimate.py`):
  - Birim `_estimate_run_cost` (4): stub cost 0, fiyat 0 cost 0,
    anthropic hesap doğrulama (8*1000=0.072 USD), max_steps ölçekleme.
  - CLI (7): insan çıktısı, JSON çıktısı, LLM çağrılmaz + audit yok,
    env `ATLAS_ESTIMATE_TOKENS_PER_CALL` override, geçersiz env
    fallback 500, `atlas run <goal>` default bit-uyumlu, bozuk goal
    YAML → exit 2.
- 1099 → **1110 yeşil**.
- mypy/ruff/scan temiz.

## Değişmeyen sözleşme

- SPEC 002/020/030/031 hepsi BİT-UYUMLU.
- `atlas run <goal>` echo demo default davranış korunur.
- `atlas run --goal-file X --dry-run` (SPEC 020) BİT-UYUMLU (action stub
  yaklaşımı; --estimate FARKLI dallanma — LLM çağırmaz).
- Batch (`--goal-file` N>1) etkilenmedi (batch içindeki tek dosya
  path'te estimate/json parametreleri iletiliyor).

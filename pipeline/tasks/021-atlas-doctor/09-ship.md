# 021 — Ship

## Sonuç
`atlas doctor` alt-komutu eklendi. Read-only env sağlık özeti stdout'a:

- **[LLM backend]** — `ATLAS_LLM` seçimi + backend-özel bilgiler
  (API key/bin var mı, model, URL). Bilinmeyen backend / eksik key
  / eksik bin → `[!]` uyarısı.
- **[Retry & fiyat]** — retries, backoff, jitter, fiyat env, trace.
- **[Depolama]** — vault, audit, sandbox, context, arşiv yaş.

**API key gizleme:** `ANTHROPIC_API_KEY` `sk-***456` gibi maskelenir;
tam key ASLA stdout'a düşmez (test regresyon güvencesi).

Exit 0 — read-only; env yanlış olsa da uyarı verir ama process'i
kırmaz.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_mask_secret, +_cmd_doctor;
                                            parser +"doctor" alt-komutu)
tests/test_cli_direct.py                  (+5 test — stub varsayılan,
                                            anthropic key yok uyarı,
                                            key mask (tam key stdout'ta YOK),
                                            claude bin yok uyarı,
                                            bilinmeyen backend uyarı)
pipeline/tasks/021-atlas-doctor/*.md      (5 artefakt)
```

## Sözleşme değişmezliği
- Mevcut alt-komutlar (`context`, `remember`, `recall`, `run`, `reindex`,
  `workflow`, `audit-verify`, `scan`, `archive`) hiç değişmedi.
- Yeni exit kodu YOK — 0 (başarı).

## Kalite kapıları
- pytest: **486 passed** (481 → +5)
- mypy strict + ruff: temiz
- `atlas scan src`: sır yok (API key mask savunması)

## Branch
`feat/021-atlas-doctor` — 020 üstünde tek commit.

## Kullanım örneği
```bash
$ atlas doctor
=== ATLAS doctor — env sağlık kontrolü ===

[LLM backend]
  ATLAS_LLM: anthropic
  ANTHROPIC_API_KEY: sk-***abc
  ATLAS_LLM_MODEL: claude-3-5-sonnet-latest
  ATLAS_LLM_ANTHROPIC_URL: (varsayılan: ...)
  ATLAS_LLM_TIMEOUT: 60s

[Retry & fiyat]
  ATLAS_LLM_RETRIES: 3 (0 = kapalı)
  ATLAS_LLM_BACKOFF: 1.0s
  ATLAS_LLM_JITTER: 0.5s (0 = kapalı)
  ATLAS_LLM_PRICE_IN:  3 $/M token
  ATLAS_LLM_PRICE_OUT: 15 $/M token
  ATLAS_LLM_TRACE: açık
  ATLAS_LLM_OBS_CHARS: 200

[Depolama]
  ATLAS_VAULT: vault
  ATLAS_AUDIT: .atlas/audit.jsonl
  ATLAS_SANDBOX: .atlas/sandbox
  ATLAS_CONTEXT: on
  ATLAS_ARCHIVE_AGE_DAYS: 7 gün
```

## Bekleyen
- 021.1: `--json` çıktı formatı (script/CI için)
- 021.2: LLM ping (küçük "hello" request ile canlılık) — cost/gecikme
- 021.3: Otomatik `.env` yükleme (`python-dotenv` veya benzeri)

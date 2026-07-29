# 021.2 — Ship

## Sonuç
`atlas doctor --ping` bayrağı eklendi. Anthropic'e minimum "hello"
request'i atar (max_tokens=8, timeout 10s sabit); latency ve token
kullanımını raporlar.

Backend anthropic değilse `[!] --ping yalnız anthropic backend'de
çalışır` uyarısı; hata (URLError/HTTPError/timeout) → warnings +
exit 0.

## Dosyalar
```
src/atlas_core/cli.py                     (edit: +_PING_TIMEOUT_S/
                                            _PING_MAX_TOKENS sabitleri;
                                            +_run_anthropic_ping ~80 sat;
                                            _cmd_doctor --ping dallanma;
                                            insan format [Ping] bölümü;
                                            parser --ping flag)
tests/test_cli_direct.py                  (+4 test — non-anthropic uyarı,
                                            happy insan format,
                                            URLError uyarı, JSON çıktısında ping)
pipeline/tasks/021-2-doctor-ping/*.md     (5 artefakt)
```

## Sözleşme değişmezliği
- `atlas doctor` (021), `atlas doctor --json` (021.1) mevcut yollar
  hiç değişmedi.
- Ping opsiyonel — varsayılan davranış bit-uyumlu.
- Exit 0 korundu.

## Kalite kapıları
- pytest: **498 passed** (494 → +4)
- mypy strict + ruff: temiz

## Branch
`feat/021.2-doctor-ping` — 021.1 üstünde tek commit.

## Kullanım örneği
```bash
$ atlas doctor --ping
=== ATLAS doctor — env sağlık kontrolü ===

[LLM backend]
  ...

[Ping]
  latency: 234ms
  input_tokens: 8
  output_tokens: 3
  cost_estimate: $0.000045
```

```bash
$ atlas doctor --ping --json | jq '.ping.latency_ms'
234
```

# 003.1 — Plan

## Adımlar (7)
1. **planner.py — anthropic:** `_call_anthropic()` + `_anthropic_planner()`
   + `_resolve_anthropic_env()` yardımcıları; `make_planner` `"anthropic"`
   dallanması. (Risk: urlopen exception ağacı Windows'ta özellik gösterir;
   test tarafında monkeypatch güvenli.)
2. **planner.py — acp:** `_resolve_acp_bin()`, `_acp_planner()`,
   `_call_acp()`, `_read_acp_line()` yardımcıları; `Popen` kaynağı
   `try/finally` ile ölür. **Risk: subprocess pipe deadlock**
   → readline hat-tamponlu + monotonic timeout ile ele alınır.
3. **Test — anthropic:** `tests/test_planner_anthropic.py`
   (AC1-AC11, ~10 test). `urllib.request.urlopen` monkeypatch;
   `HTTPError`/`URLError`/`socket.timeout` her biri için ayrı test.
4. **Test — acp:** `tests/test_planner_acp.py` (AC12-AC20, ~8 test).
   Fake `Popen` yardımcı sınıfı: `stdin.write`, `stdout.readline`,
   `stderr.read`, `wait`, `kill` — hepsi kaydeder; script'lenmiş
   satır listesi ile deterministik davranış.
5. **Test — CLI + regresyon:** `test_planner.py` bilinmeyen backend
   testi güncellenir (anthropic/acp artık NotImpl DEĞİL); yeni test:
   `ATLAS_LLM=xyz` mesaj içeriğinde "anthropic" ve "acp" görünür.
   `test_cli_direct.py`'e "anthropic key yok → exit 7" testi.
6. **Kalite kapıları:** ruff, mypy strict, pytest --cov. Coverage
   ≥ %90.
7. **Ship + DECISIONS:** `09-ship.md` + DECISIONS 2026-07-29 altında
   iki [KARAR] girdisi (anthropic urllib kalıbı; acp stdio ACP-lite).

## Kanıt (test → dosya eşleşmesi)
| Kabul | Test | Dosya |
|---|---|---|
| AC1-AC11 | test_planner_anthropic.py::* | planner.py::_anthropic_planner |
| AC12-AC20 | test_planner_acp.py::* | planner.py::_acp_planner |
| AC21 | test_cli_direct.py::test_exit_7_anthropic_key_yok | cli.py |
| AC22 | test_planner.py::test_llm_bilinmeyen_backend | planner.py |
| AC23 | pytest --cov + mypy + ruff | tümü |

## Zaman
- 1-2: 60-90 dakika (asıl kod + tuzaklar)
- 3-4: 45-60 dakika (test iskeleleri + fake sınıflar)
- 5: 15 dakika
- 6-7: 15 dakika

## Risk & Azaltma
- **Windows subprocess pipe stalling:** `bufsize=1` + `text=True` +
  monotonic timeout + `readline`. Test tarafı `Popen` monkeypatch
  yapıp gerçek pipe kullanmaz.
- **API key sızıntısı:** Hiçbir kod yolunda key stderr/audit/log'a
  yazılmaz; test bunu doğrulayan bir assertion içerir.
- **JSON-RPC deviation:** Test için basitleştirilmiş request/response
  eşleşmesi; agent'ın gönderebileceği `available_commands_update` gibi
  notification'lar sessizce yok sayılır (yalnız `agent_message_chunk`
  ve `id=3` cevabı önemli).

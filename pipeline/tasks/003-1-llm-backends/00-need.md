# 003.1 — İhtiyaç: `anthropic` ve `acp` LLM backend'leri

## Bağlam
Görev 003 (2026-07-29) `ATLAS_LLM=claude` backend'ini `claude --print`
subprocess'iyle canlandırdı; `ATLAS_LLM=acp` ve `ATLAS_LLM=anthropic`
açık `NotImplementedError("Görev 003.1'de eklenecek")` ile bırakıldı.
Bu görev, iki backend'i minimum yeterli implementasyonla kapatır:
- **anthropic:** doğrudan Anthropic Messages API üzerinden HTTPS POST
  (stdlib `urllib`+`ssl`); yerel `claude` kurulumu şart değil.
- **acp:** ATLAS/Juggler ekosisteminde standart olan **Agent Client
  Protocol**'un stdio (subprocess) alt kümesi — `initialize` →
  `session/new` → `session/prompt` → ilk `agent_message` metnini al →
  kapan. Görev başına tek-oturum; kalıcı bağlantı yok.

## İhtiyaç (tek cümle)
`ATLAS_LLM=anthropic` ve `ATLAS_LLM=acp` verildiğinde planner, sırasıyla
Anthropic REST API'sini ve stdio ACP alt-agent'ını çağırıp her turun
planını gerçek bir LLM'den alsın; hata dallanması Görev 003
sözleşmesindekiyle (`LLMPlannerError` + exit 7) birebir aynı olsun.

## Ölçülebilir Başarı
- **M1 — anthropic happy:** `ATLAS_LLM=anthropic` + `ANTHROPIC_API_KEY=...`
  altında `make_planner(goal)` gerçek callable döner; monkeypatch edilen
  `urllib.request.urlopen` fake `{"content":[{"type":"text",
  "text":"write:x.txt:1"}]}` cevabı verirse planner `"write:x.txt:1"`
  döndürür.
- **M2 — anthropic env sözleşmesi:** `ANTHROPIC_API_KEY` yoksa fabrika
  anında `LLMPlannerError("ANTHROPIC_API_KEY yok")`; `ATLAS_LLM_MODEL`
  (varsayılan `claude-3-5-sonnet-latest`) ve `ATLAS_LLM_TIMEOUT`
  (varsayılan 60) mevcut kalıba uyar.
- **M3 — anthropic HTTP hataları:** 4xx/5xx → `LLMPlannerError("HTTP
  <code>: <ilk 200 karakter body>")`; `URLError`/`socket.timeout` →
  `LLMPlannerError("anthropic başlatılamadı: ...")` /
  `LLMPlannerError("timeout: <n>s aşıldı")`.
- **M4 — anthropic boş cevap:** `content` boş liste, `text` boş string
  veya JSON parse hatası → `LLMPlannerError("boş plan")`/`LLMPlannerError(
  "geçersiz JSON: ...")`.
- **M5 — acp happy:** `ATLAS_LLM=acp` + `ATLAS_LLM_ACP_BIN=<sahte bin>`
  altında, monkeypatch edilen `subprocess.Popen` sahte stdio
  (`initialize` yanıtı → `session/new` yanıtı → `session/update` ile
  `agent_message_chunk("write:x.txt:1")` → `stop`) planner'ı bir plan
  satırı üretmeye götürür.
- **M6 — acp env sözleşmesi:** `ATLAS_LLM_ACP_BIN` yoksa fabrika anında
  `LLMPlannerError("acp agent bin bulunamadı: ...")`; timeout env'i
  paylaşılır (`ATLAS_LLM_TIMEOUT`, varsayılan 60).
- **M7 — acp hata:** subprocess exit!=0, stderr taşınır; JSON-RPC
  cevabında `error` alanı → `LLMPlannerError("acp error: <mesaj>")`;
  timeout → `LLMPlannerError("timeout")`; süreç her yolda kill'lenir
  (kalıntı Popen yok).
- **M8 — Sözleşme uyumu:** Görev 006 (`context=` kwarg) her iki
  backend'e uygulanır; verilirse prompt/mesaj gövdesine "Önceden bilinen
  bağlam" bloğu eklenir (mevcut `_format_prompt` yardımcı fonksiyonunun
  yeniden kullanımı).
- **M9 — Test kapsamı:** iki yeni test dosyası (`test_planner_anthropic.py`,
  `test_planner_acp.py`) ~18 test; `test_planner.py` bilinmeyen backend
  testi güncellenir; `test_cli_direct.py` exit 7 için genişler. Toplam
  test 319 → ~337; coverage ≥ %90 (baseline %94.85).
- **M10 — DECISIONS:** anthropic HTTP + acp stdio kalıbı 2026-07-29
  altına ayrı [KARAR] girdileri.

## Kapsam DIŞI
- ACP tool-use, streaming, permissions dialog — minimum text-only
  akış yeterli.
- Anthropic tool-use, vision, prompt caching, streaming — kapsam dışı.
- Retry/backoff — Görev 013 (planlanmış). Bu görevde tek deneme.
- Cost/token muhasebesi — Görev 011.
- API anahtarı `.env` entegrasyonu — kullanıcı env değişkenini
  kendi kabuğundan set eder; ATLAS okur, saklamaz.

## Kısıt
- `Planner`, `make_planner`, `PlannerExhaustedError`, `LLMPlannerError`
  imzaları değişmez.
- Yeni bağımlılık YOK: stdlib `urllib.request`, `urllib.error`,
  `ssl`, `json`, `subprocess`, `os`.
- Windows locale/cp1254 tuzağı: subprocess çağrılarında
  `encoding="utf-8", errors="replace"` sabit (DECISIONS 2026-07-24
  kalıbı devralınır).
- İstisna adları `*Error` sonekli.
- Türkçe hata mesajları.

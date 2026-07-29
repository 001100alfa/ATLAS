# 003.1 — SPEC: anthropic + acp LLM backend'leri

**Sözleşme değişmezliği:** `orchestrator/core.py::{run_loop, Action,
Judge, CallBudget, LoopResult, StepKind}` ve `orchestrator/planner.py::
{Planner, make_planner, PlannerExhaustedError, LLMPlannerError}` imzaları
korunur. Yeni yalnızca **iç** (modül-özel) yardımcı fonksiyonlar eklenir.

## 1. Fonksiyonel Gereksinimler

### FR1 — Backend seçim genişlemesi
`ATLAS_LLM` değişkeninde `anthropic` ve `acp` artık **NotImplementedError
fırlatmaz**; ilgili planner fabrikasına yönlendirir. Bilinmeyen değer
hâlâ `NotImplementedError` fırlatır (mesaj metni güncellenir:
`"desteklenen: stub, claude, anthropic, acp"`).

### FR2 — `anthropic` backend

**Env sözleşmesi:**
| Değişken | Varsayılan | Anlam |
|---|---|---|
| `ANTHROPIC_API_KEY` | (yok) | Zorunlu; yoksa fabrika anında hata |
| `ATLAS_LLM_MODEL` | `claude-3-5-sonnet-latest` | Anthropic model id |
| `ATLAS_LLM_TIMEOUT` | `60` | Saniye — mevcut sözleşmeye uyar |
| `ATLAS_LLM_ANTHROPIC_URL` | `https://api.anthropic.com/v1/messages` | Test/vekil için override |

**HTTP çağrısı:**
- `POST <URL>`, `Content-Type: application/json`,
  `x-api-key: <ANTHROPIC_API_KEY>`, `anthropic-version: 2023-06-01`.
- Gövde: `{"model": <ATLAS_LLM_MODEL>, "max_tokens": 256,
  "messages": [{"role":"user","content": <_format_prompt(...)>}]}`.
- `urllib.request.Request` + `urllib.request.urlopen(req, timeout=...)`.
- `ssl.create_default_context()` — sistem sertifikaları kullanılır.
- Response body UTF-8; JSON parse.

**Yanıt çözümlemesi:**
- `data["content"]` bir liste; `type == "text"` olan ilk elemanın
  `text` alanının **ilk satır**ı alınır (mevcut `claude` planner
  ile aynı kalıp — çok satırlı yanıt → ilk satır).
- Boş içerik / metin → `LLMPlannerError("boş plan")`.

**Hata dallanması → hepsi `LLMPlannerError`:**
- `HTTPError` (4xx/5xx): `"HTTP <code>: <ilk 200 karakter body>"`.
- `URLError` (network): `"anthropic başlatılamadı: <sebep>"`.
- `socket.timeout` (veya `TimeoutError`): `"timeout: <n>s aşıldı"`.
- `json.JSONDecodeError`: `"geçersiz JSON: <ilk 200 karakter>"`.
- Beklenmeyen yapı (content yok, text yok): `"anthropic beklenmedik
  yanıt yapısı"`.

**Fabrika seviyesi hata (fail-fast):**
- `ANTHROPIC_API_KEY` boş → `LLMPlannerError("ANTHROPIC_API_KEY yok:
  ortam değişkeni set edin")`; `make_planner` **çağrı anında** patlar.

### FR3 — `acp` backend

**Env sözleşmesi:**
| Değişken | Varsayılan | Anlam |
|---|---|---|
| `ATLAS_LLM_ACP_BIN` | (yok) | Zorunlu; yoksa fabrika anında hata |
| `ATLAS_LLM_ACP_ARGS` | (boş) | Boşlukla ayrılmış ek argümanlar |
| `ATLAS_LLM_TIMEOUT` | `60` | Toplam timeout (subprocess yaşam süresi) |

**Fabrika seviyesi çözümleme:**
- `ATLAS_LLM_ACP_BIN` verildiyse: `os.path.isfile` doğrulaması;
  yoksa: `shutil.which(name)` PATH taraması. Bulunamazsa
  `LLMPlannerError("acp agent bin bulunamadı: PATH'e ekleyin veya
  ATLAS_LLM_ACP_BIN ile mutlak yolu verin")`.

**Protokol (ACP-lite, text-only):**

Her plan çağrısı için **kısa oturum**:
1. `subprocess.Popen([bin, *args], stdin=PIPE, stdout=PIPE, stderr=PIPE,
   text=True, encoding="utf-8", errors="replace", bufsize=1)` — hat-tamponlu.
2. `initialize` request (JSON-RPC 2.0): `{"jsonrpc":"2.0","id":1,
   "method":"initialize","params":{"protocolVersion":1,
   "clientCapabilities":{}}}\n` — stdin'e yazılır.
3. Cevap `id:1` — hataysa `LLMPlannerError`.
4. `session/new` request `id:2`: `{"method":"session/new",
   "params":{"cwd":<os.getcwd()>,"mcpServers":[]}}\n`. Yanıtta
   `sessionId` alınır; hata → `LLMPlannerError`.
5. `session/prompt` request `id:3`: `{"method":"session/prompt",
   "params":{"sessionId":<id>,"prompt":[{"type":"text",
   "text":<_format_prompt(...)>}]}}\n`.
6. Agent tarafından gelen JSON satırları oku:
   - `method == "session/update"` **notification**'larından
     `update.sessionUpdate == "agent_message_chunk"` olanların
     `content.text` alanları birleştirilir.
   - `id:3` cevabı (`stopReason` içerir) gelene kadar oku.
   - `error` alanı → `LLMPlannerError`.
7. Toplanan metin `strip().splitlines()[0]` → ilk satır.
   Boşsa `LLMPlannerError("boş plan")`.
8. `finally`: stdin kapa; process `wait(timeout=2)`; hâlâ ölmediyse
   `kill()`. **Süreç sızıntısı yasak.**

**Timeout:** `time.monotonic()` başlatılır; her `readline` öncesi
kalan süre hesaplanır; aşılırsa `LLMPlannerError("timeout")` +
`proc.kill()`.

**Hata dallanması → `LLMPlannerError`:**
- `FileNotFoundError`/`OSError` (Popen): `"acp başlatılamadı: <sebep>"`.
- `TimeoutError`: `"timeout: <n>s aşıldı"`.
- JSON parse: `"acp: geçersiz JSON satır: <ilk 200>"`.
- JSON-RPC error: `"acp error: <error.message>"`.
- Subprocess erken kapandı (exit!=0 stdout tükendiyken): `"acp exit=<rc>: <stderr ilk 200>"`.

### FR4 — Prompt paylaşımı (bakım maliyeti minimize)
`_format_prompt(goal, history, context=None)` mevcut yardımcı
**anthropic** ve **acp** için de kullanılır. Her ikisi de aynı prompt
gövdesini kabul eder:
- anthropic: `messages[0].content`
- acp: `session/prompt.params.prompt[0].text`

Bu, Görev 006 (context injection) sözleşmesini iki backend'e
otomatik taşır.

### FR5 — CLI değişmez
`cli.py::_cmd_run_goal` `LLMPlannerError` yakalama noktası mevcut
(Görev 003). Yeni backend'ler aynı istisnayı fırlattığından **CLI
kodunda değişiklik gerekmez**. Sadece `.md` env sözleşmesi güncellenir.

### FR6 — Geriye uyumluluk
- `ATLAS_LLM=stub` (varsayılan) davranışı bit-uyumlu.
- `ATLAS_LLM=claude` (Görev 003) davranışı bit-uyumlu.
- Mevcut YAML'lar hiç değişmez.

## 2. Arayüz Sözleşmeleri

```
src/atlas_core/orchestrator/planner.py                     (edit)
  # Mevcut korunanlar:
  #   Planner, PlannerExhaustedError, LLMPlannerError, make_planner,
  #   _resolve_claude_bin, _format_prompt, _call_claude, _claude_planner
  # Yeni iç (public API değil):
  def _anthropic_planner(goal, context=None) -> Planner
  def _call_anthropic(api_key, url, model, prompt, timeout_s) -> str
  def _resolve_acp_bin() -> tuple[str, list[str]]
  def _acp_planner(goal, context=None) -> Planner
  def _call_acp(bin_path, argv_extra, prompt, timeout_s) -> str
  # make_planner içindeki `raise NotImplementedError` yerine
  #   backend "anthropic" -> _anthropic_planner(...)
  #   backend "acp"       -> _acp_planner(...)

tests/test_planner_anthropic.py    (yeni, ~10 test)
tests/test_planner_acp.py          (yeni, ~8 test)
tests/test_planner.py              (edit: bilinmeyen backend mesajı güncellendi;
                                   acp+anthropic NotImplementedError testi kaldırıldı)
tests/test_cli_direct.py           (edit: +1 test — anthropic env yok/exit 7)

pipeline/tasks/003-1-llm-backends/*.md    (yeni artefaktlar)
```

## 3. Kabul Kriterleri

### Anthropic
- **AC1 — Fabrika (env dolu):** `ATLAS_LLM=anthropic` + `ANTHROPIC_API_KEY=k` →
  `make_planner(goal)` callable döner.
- **AC2 — Key yok:** `ANTHROPIC_API_KEY` yok/boş → `LLMPlannerError` fabrika anında.
- **AC3 — Happy call:** `urlopen` monkeypatch, `{"content":[{"type":"text",
  "text":"write:x.txt:1\n"}]}` → planner "write:x.txt:1" döner. Header'da
  `x-api-key` ve `anthropic-version` bulunmalı; gövdede model + prompt.
- **AC4 — Timeout:** `urlopen` `socket.timeout` fırlatır → `LLMPlannerError`
  içeriği "timeout" + saniye.
- **AC5 — HTTPError:** `HTTPError(code=429, body=b"rate limit")` →
  `LLMPlannerError("HTTP 429" + "rate limit")`.
- **AC6 — URLError:** `URLError("dns")` → `LLMPlannerError` içerir
  "anthropic başlatılamadı" + "dns".
- **AC7 — Geçersiz JSON:** stdout `b"<html>500</html>"` → `LLMPlannerError`
  içerir "geçersiz JSON".
- **AC8 — Boş içerik:** `{"content":[]}` → `LLMPlannerError("boş plan")`.
- **AC9 — Çok satır:** text = "line1\nline2" → planner "line1".
- **AC10 — UTF-8:** text "write:çıkış.txt:merhaba 🚀" → planner aynı.
- **AC11 — Context 006:** `context="..."` verilirse gövdedeki
  `messages[0].content` metninde "Önceden bilinen bağlam" bloğu olur.

### ACP
- **AC12 — Fabrika (bin var):** `ATLAS_LLM=acp` + `ATLAS_LLM_ACP_BIN=<sahte>`
  → callable döner.
- **AC13 — Bin yok (env + PATH):** `LLMPlannerError` fabrika anında,
  mesaj "acp agent bin bulunamadı" içerir.
- **AC14 — Happy call:** monkeypatch edilen `Popen` fake stdout
  akışıyla `agent_message_chunk` iki parçada yollar → planner
  birleştirilmiş ilk satırı döner.
- **AC15 — JSON-RPC error:** `initialize` yanıtı `"error":{"code":-1,
  "message":"unauthorized"}` → `LLMPlannerError("acp error: unauthorized")`.
- **AC16 — Timeout:** monkeypatch `readline` sonsuz bekler → planner
  `LLMPlannerError("timeout")` + fake proc `kill()` çağrıldı.
- **AC17 — Erken exit:** Popen `returncode=2` erken → `LLMPlannerError`
  "acp exit=2" + stderr içerir.
- **AC18 — Boş yanıt:** hiç `agent_message_chunk` gelmez, sadece `stopReason`
  → `LLMPlannerError("boş plan")`.
- **AC19 — UTF-8:** chunk `"write:çıkış.txt:🚀"` → planner aynı.
- **AC20 — Context 006:** `context="..."` → `session/prompt` gövdesinde
  "Önceden bilinen bağlam" bulunur.

### CLI + genel
- **AC21 — Exit 7 (in-process):** `_cmd_run_goal` `LLMPlannerError`
  yakalar → main(...) = 7 (mevcut test genişletilerek anthropic key-yok
  senaryosu eklenir).
- **AC22 — Bilinmeyen backend mesajı:** `ATLAS_LLM=xyz` → `NotImplementedError`
  içerik "desteklenen: stub, claude, anthropic, acp".
- **AC23 — Kalite kapıları:** ruff + mypy strict + pytest yeşil;
  coverage ≥ %90.

## 4. Q → Kararlar

- **Q1 — Neden `anthropic` için `httpx`/`requests` değil?** Bağımlılık
  sıfır tutulur; `urllib` bu iş için yeter. Test edilebilirlik
  monkeypatch ile aynı.
- **Q2 — ACP tam mı yoksa alt-küme mi?** Alt-küme (initialize + session
  + text prompt/reply). Tool-use/permissions Görev 010+.
- **Q3 — ACP oturum-per-plan yerine kalıcı bağlantı?** Şu an
  oturum-per-plan; kalıcı bağlantı planner sözleşmesinin durumsal
  hâle gelmesini gerektirir (state fabrika-dışı). Görev 013+.
- **Q4 — API key logging?** Anthropic key stderr/audit'e **yazılmaz**;
  yalnız header'a girer. Kayıt geçerse sır sızar (DECISIONS 2026-07-29
  kalıbı).
- **Q5 — Model ismi neden env'de sabit?** `Goal.llm_model` opsiyonel
  alanı Görev 003.3'e ertelendi; env yolu her iki backend için
  şu an yeterli.
- **Q6 — Retry?** Yok (Görev 013). Tek deneme sözleşmesi devam.

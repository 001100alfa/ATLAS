# 016.1 — İhtiyaç: ACP `fs/read_text_file` minimum destek

## Bağlam
SPEC 016 ACP `tool_call`/`tool_call_update` bildirimlerine **açık red**
verdi — agent tool istediğinde hemen `LLMPlannerError` fırlıyor.
Ancak ACP protokolünde ayrıca **client-provided methods** var: agent
bir JSON-RPC **request** gönderir (`method: fs/read_text_file`),
client cevap verir. Bunlar `tool_call` (agent'ın kendi bildirimi)
değildir; ATLAS'ın 016 dispatcher'ı bunları görmez → agent
`fs/read_text_file` request'i gönderse ATLAS **cevap vermez** →
subprocess sonsuz bekler → timeout.

Minimum yeterli düzeltme: agent'ın **read-only** dosya okuma isteğine
proje kökünden güvenli yol çözümüyle cevap ver. Yazma / shell isteklerine
JSON-RPC error dön (izin yok).

## İhtiyaç (tek cümle)
`_call_acp` okuma döngüsünde `method == "fs/read_text_file"` (ve
diğer client-provided istekler) yakalasın; okuma isteğine gerçek
dosya içeriğiyle cevap versin; yazma/shell isteklerine error dönsün;
tanınmayan method'lara `-32601 Method not found` yollayıp devam etsin.

## Ölçülebilir Başarı
- **M1 — Method tanıma:** `msg.get("method")` set edilmiş VE
  `id` var → request. `fs/read_text_file`, `fs/write_text_file`,
  `terminal/create` gibi client-method'lar handler tablosuna gider.
- **M2 — `fs/read_text_file` uygulaması:**
  - `params.path` mutlak yol; `os.getcwd()` altındaysa (yol traversali
    engelli) `Path(path).read_text(encoding="utf-8", errors="replace")`
    döner.
  - Kök dışıysa `-32000 permission denied` error.
  - Dosya yoksa `-32000 file not found` error.
  - `params.line` / `params.limit` (offset/count) opsiyonel — verilirse
    satır aralığı; verilmezse tümü.
  - Response: `{"jsonrpc":"2.0","id":<X>,"result":{"content":<text>}}`.
- **M3 — Yazma/shell red:** `fs/write_text_file`, `terminal/create`,
  `terminal/output`, `terminal/wait_for_exit`, `terminal/kill`,
  `terminal/release` gibi metotlara `-32000 not supported` error
  cevabı; süreç kırılmaz, döngü devam eder.
- **M4 — Bilinmeyen method:** `-32601 Method not found` (JSON-RPC
  standardı) + döngü devam.
- **M5 — Notification olan `session/update` tool_call red korunur:**
  SPEC 016 davranışı bit-uyumlu — tool_call notification'ı hâlâ
  sert red (LLMPlannerError). fs/read_text_file **request** ise
  cevap verilir. İki mekanizma ayrı.
- **M6 — Test:** +6 test — happy read, yol traversal red, dosya yok,
  write red, bilinmeyen method (-32601), tool_call notif hâlâ red.
- **M7 — DECISIONS:** [KARAR] neden read-only; neden proje kökü
  sınırı.

## Kapsam DIŞI
- Permission dialog (`session/request_permission`) — auto-allow
  read-only politikası; UI kısmı YAGNI.
- Terminal desteği — güvenlik burden'ı büyük.
- `fs/write_text_file` (`--dangerously-skip-permissions` senaryosu
  bile) — 016.2+.
- MCP forwarding — 016.3+.

## Kısıt
- `_call_acp` sözleşmesi korunur.
- Proje kökü sabit `os.getcwd()` — override yok (test tarafında
  monkeypatch).
- Yol traversal denetimi: `Path(path).resolve()`'in `Path.cwd().
  resolve()`'un alt ağacında olması.
- Türkçe hata mesajı iç mesajlar için; JSON-RPC error `message`
  agent'a İngilizce dönebilir (ACP sözleşmesi).

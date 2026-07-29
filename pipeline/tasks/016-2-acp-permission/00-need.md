# 016.2 — İhtiyaç: ACP `session/request_permission` handler

## Bağlam
SPEC 016.1 client-provided method desteği (`fs/read_text_file`)
verdi. Ancak ACP protokolünde agent, tool çalıştırmadan **önce**
`session/request_permission` request'i gönderebilir — client'ın
onayını ister. Client cevap vermezse agent bekler; şu an ATLAS
bu request'e `-32601 Method not found` diyor → agent boş cevap
alıyor.

## İhtiyaç (tek cümle)
`session/request_permission` request'ine tool tipine göre otomatik
karar dön: read-only tool'lara `allow_once`, write/shell tool'larına
`reject`; kullanıcı UI dialogu asla görmez.

## Ölçülebilir Başarı
- **M1 — Method tanıma:** `msg.method == "session/request_permission"`
  → özel yol. `params.toolCall.name` (veya `title`) tool adını
  verir; `params.options` seçenek listesi.
- **M2 — Karar mantığı:** tool adı `_ACP_READ_METHODS` içindeyse
  (`fs/read_text_file`) `allow_once` seç; `_ACP_WRITE_METHODS` içindeyse
  `reject`; bilinmeyense `reject` (savunmalı varsayılan).
- **M3 — Yanıt formatı:** `{"jsonrpc":"2.0","id":<req_id>,
  "result":{"outcome":{"outcome":"selected","optionId":"<X>"}}}`.
  Seçilen optionId önceliği: `params.options`'tan tam eşleşen ilki
  (`allow_once` > `allow_always` > `reject` > `cancelled`).
- **M4 — Fallback:** `params.options` boş/eksik → sabit `allow_once` /
  `reject` string'i sözleşme ihlali olmadan yanıtla.
- **M5 — Test:** +4 test — read tool allow, write tool reject,
  bilinmeyen tool reject, options'tan doğru id seçimi.
- **M6 — DECISIONS:** [KARAR] otomatik karar mantığı; UI dialogu
  neden yok.

## Kapsam DIŞI
- İnteraktif kullanıcı dialogu (`input()`) — ATLAS otonom ajan;
  insan-in-loop 016.3+'da.
- Karar log'u UI için — audit'e zaten yazılıyor.
- Session-level "her zaman izin ver" durumu — 016.4+.

## Kısıt
- Mevcut 016.1 `_acp_handle_client_request` dispatcher genişler.
- Yeni exception YOK.
- Türkçe iç not; JSON-RPC yanıtı ACP sözleşmesi (İngilizce alan
  adları).

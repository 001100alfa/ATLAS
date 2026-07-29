# 019.1 — İhtiyaç: ACP streaming ilk newline'da kes

## Bağlam
SPEC 019 Anthropic streaming'te `text_delta` chunk'ları biriktirilirken
**ilk newline'da kesme** uygulandı. ACP protokolü `agent_message_chunk`
notification'larıyla zaten satır satır akan bir yapı; ama şu an
`_call_acp` chunk'ları biriktirir ve `stopReason` gelene kadar okur.
Anthropic ile simetri için: ilk `\n` görüldüğünde erken çık, ACP
oturumunu kısalt.

## İhtiyaç (tek cümle)
`_call_acp` `agent_message_chunk` chunk'larını biriktirirken
`"\n" in joined_text` olur olmaz döngüden çık ve oturumu `finally`
bloğunda kapat; kalan chunk'lar okunmaz.

## Ölçülebilir Başarı
- **M1 — Erken çık:** ilk `\n` görüldüğünde `break`; `stopReason`
  gelmeden çıkabilir.
- **M2 — Süreç kill:** `finally _acp_teardown` mevcut, erken çıkışta
  da tetiklenir. Süreç sızıntısı yasak.
- **M3 — Bit-uyumlu:** tek satırlı yanıtlarda mevcut davranış aynı
  (chunk sonu `\n` gelmese bile `stopReason` gelirse toplanan text
  kullanılır).
- **M4 — İlk satır boşsa devam:** `\n` gelse ama toplanan text
  boşsa (`"\n"`) devam et — anlamlı content bekle.
- **M5 — Test:** +3 test — iki chunk arasında `\n` erken çık,
  ilk chunk boş newline devam, mevcut testler yeşil.
- **M6 — DECISIONS:** [KARAR] anthropic ile simetri; süreç kill korunur.

## Kapsam DIŞI
- ACP request'e `stream` bayrağı — protokolde native streaming
  var (chunk'lar zaten akıyor); ek bir bayrak yok.
- Tool-use streaming (016.1+ ile birlikte).

## Kısıt
- `_call_acp` sözleşmesi korundu.
- Türkçe iç yorum.

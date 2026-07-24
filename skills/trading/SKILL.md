# Trading / BIST Kuralları

## Pine Script
- v6 kullan; request.security'de lookahead=barmerge.lookahead_off.
- Strateji: komisyon ve kayma (slippage) parametreleri boş bırakılmaz.

## Veri katmanı (FastAPI desk)
- WebSocket besleme; Redis pub/sub ile fan-out.
- Sembol listesi config'te, kod içinde hardcode edilmez.
- Zaman damgaları UTC, gösterim katmanında TRT'ye çevrilir.

## Genel
- Finansal çıktılar tavsiye değil veri sunumudur; kod yorumlarına
  ve UI'a bu ayrım yazılır.

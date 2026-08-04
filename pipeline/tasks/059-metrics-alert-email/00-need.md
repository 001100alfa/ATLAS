# Görev 059 — İhtiyaç

SPEC 029 `atlas metrics --alert PCT` cache-hit oranı eşiğin altına
düşerse stderr'e UYARI basar + exit 8. CI için iyi ama:
- Cron/scheduled çalıştırmalarda stderr kimse görmez
- Production'da alert bildirimi email olmalı (Slack/webhook için ayrı
  entegrasyon, YAGNI)

## Kabul kriteri

- `atlas metrics --alert-email` bayrağı (store_true).
- `--alert PCT` ile birleşince: eşik aşılırsa (`hit_ratio < PCT`)
  stderr uyarı + SMTP email + exit 8.
- Env sözleşmesi:
  - `ATLAS_SMTP_HOST` (zorunlu)
  - `ATLAS_SMTP_PORT` (default 587)
  - `ATLAS_SMTP_USER` / `ATLAS_SMTP_PASSWORD` (opsiyonel)
  - `ATLAS_SMTP_STARTTLS` (default "1" — 1/true/yes = TLS)
  - `ATLAS_ALERT_FROM` (zorunlu)
  - `ATLAS_ALERT_TO` (zorunlu, virgülle liste)
- Email içeriği:
  - Subject: `[ATLAS] metrics alert: cache-hit X.X% < Y.Y%`
  - Body: UYARI satırı + token toplamları özet
- Env eksik/SMTP hata → stderr'e `[alert-email] gönderim başarısız: ...`
  ama exit 8 KORUR (alert semantik önemli, email yan etki).
- `--alert-email` yalnız başına (--alert olmadan) etkisiz.
- SPEC 029 `--alert PCT` bayraksız veya --alert-email yoksa BİT-UYUMLU.

## Riskli

- SMTP kurulumu üretim ortamı gerektirir — test için `smtplib.SMTP`
  monkeypatch (`_FakeSMTP` sınıfı).
- Slack/webhook için ayrı SPEC (059 sadece email).
- Kimlik bilgisi env'de ham → shell history riski. Kullanıcı `.env`
  dosyası önerilir (ATLAS zaten `.env` yükler; secret kayıtta bozar
  ama runtime'da yükler).

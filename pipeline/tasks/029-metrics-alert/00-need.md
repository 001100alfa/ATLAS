# 029 — İhtiyaç: `atlas metrics --alert <PCT>`

## Bağlam
023 `atlas metrics` cache-hit oranını basıyor ama insan gözü ile
okunuyor. CI/pre-flight bir eşik altında kalırsa uyarı ister — hem
maliyet artıyor (cache boşuna dönmüyor) hem de bir 015 regresyonu
işareti olur. Eşiğin altındaki durumu **exit kodu** ile bildirmek
lazım ki CI job durabilsin.

## İhtiyaç (tek cümle)
`atlas metrics --alert 20` — cache-hit oranı %20 altındaysa `stderr`'e
uyarı bas ve `exit 8` dön; üstündeyse `exit 0`.

## Ölçülebilir Başarı
- **M1 — Bayrak:** `atlas metrics --alert PCT` (`float`, 0–100).
  Verilmezse mevcut davranış (alarm yok).
- **M2 — Eşik altı:** oran (`total_cr / (total_in + total_cc +
  total_cr)`) < PCT → stderr `UYARI: cache-hit %X.X < eşik %Y.Y` +
  `exit 8` (yeni exit kodu).
- **M3 — Eşik üstü:** oran ≥ PCT → mevcut çıktı + `exit 0`.
- **M4 — Kayıt yok:** metrics.jsonl boş/yoksa `hit_ratio = 0.0`;
  `--alert` verilmişse 0 < PCT olduğundan alarm KAÇINILMAZ (kural:
  "veri yok da uyarıdır"). `--alert 0` verilirse alarm yok (kapalı).
- **M5 — `--json` uyumu:** `--json` ile birleşir; JSON çıktısı olduğu
  gibi (liste) basılır, uyarı stderr'e gider, exit kodu aynı kurala
  tabidir.
- **M6 — Sınır kontrolü:** `PCT < 0` veya `PCT > 100` → SPEC HATASI +
  exit 2 (mevcut sözleşme).
- **M7 — Test:** +5 test (alt geçer, üst düşer, kayıtsız+alert
  düşer, --json ile birleşir, mesaj formatı + sınır).
- **M8 — DECISIONS:** [KARAR] yeni exit kodu 8 = "alert eşiği
  geçilemedi"; neden 6 değil (6 archive-all failed, farklı semantik).

## Kapsam DIŞI
- Renkli çıktı — kapsam dışı.
- Otomatik e-posta/slack bildirim — env dışı, işletmen görevi.
- Alarm günlüğü (`.atlas/alerts.jsonl`) — YAGNI, exit kod yeter.
- Cache dışı metrikler için alarm (input tokens vb.) — 029.1
  kapsamı.

## Kısıt
- `_cmd_metrics` mevcut çıktı sözleşmesi korunur; alarm eklenir,
  hiçbir metin silinmez.
- `--limit` etkileşimi: alarm `--limit`'ten sonra hesaplanır (yani
  tail'in oranı denetlenir — mevcut cache-hit hesabı da tail üzerine).
- Türkçe uyarı mesajı.
- Yeni env DEĞİL, yeni CLI bayrağı.

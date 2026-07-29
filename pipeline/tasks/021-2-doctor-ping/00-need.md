# 021.2 — İhtiyaç: `atlas doctor --ping` canlılık kontrolü

## Bağlam
SPEC 021 env okur; SPEC 021.1 JSON verir; ama **gerçekten çalışıyor mu?**
sorusunu cevaplamıyor. Kullanıcı Anthropic'e minimal request atmadan
API key doğru mu, model erişilebilir mi bilmiyor. `--ping` bayrağı
minimum "hello" request'i atsın; latency + status + tahmini cost
raporlasın.

## İhtiyaç (tek cümle)
`atlas doctor --ping` verildiğinde anthropic backend'e kısa bir
"hello" request'i atılsın (max_tokens=8, kısa timeout 10s); yanıt
alınırsa `latency_ms`, `input_tokens`, `output_tokens`,
`cost_estimate` raporlansın; hata alırsa `[!]` uyarısı verilip
exit 0.

## Ölçülebilir Başarı
- **M1 — Bayrak:** `atlas doctor --ping` — sadece anthropic'te
  anlamlı. Diğer backend'lerde `[!] --ping yalnız anthropic
  backend'de çalışır` uyarı + hiç request atma.
- **M2 — Payload:** `{"model": <resolved>, "max_tokens": 8,
  "messages": [{"role":"user","content":"hello"}]}`. Sistem prompt
  YOK, streaming YOK — minimum ping.
- **M3 — Timeout:** 10s sabit — env'i yok say (hızlı feedback).
- **M4 — İnsan format:** yeni satır
  ```
  [Ping]
    latency: 234ms
    input_tokens: 8
    output_tokens: 3
    cost_estimate: $0.000010
  ```
- **M5 — JSON format:** `--ping --json` → rapor'a `"ping"` alanı
  ekle.
- **M6 — Hata:** LLM hatası (auth, timeout, 4xx/5xx) yakalanır,
  warnings'e `ping başarısız: <mesaj>` eklenir; exit 0 (021 kalıbı).
- **M7 — Test:** +4 test — anthropic olmayan backend'de --ping
  uyarısı, happy ping (urlopen mock), hata (URLError), JSON çıktısında
  ping alanı.
- **M8 — DECISIONS:** [KARAR] neden sabit 10s; neden max_tokens=8.

## Kapsam DIŞI
- claude/acp backend ping — subprocess başlatmak pahalı; anthropic
  yeter.
- Batch ping (birden fazla model test) — YAGNI.
- Ping'te retry (008 zinciri) — çalıştırmıyoruz; ping tek deneme,
  hızlı hata.

## Kısıt
- Anthropic'e gerçek network request — test'te `urlopen` monkeypatch.
- Cost hesabı `_fmt_cost` mevcut yolla.
- Türkçe uyarı.

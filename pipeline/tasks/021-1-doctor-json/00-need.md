# 021.1 — İhtiyaç: `atlas doctor --json`

## Bağlam
SPEC 021 `atlas doctor` insan-okunur çıktı verir. CI / pre-flight
script'leri için parse edilebilir JSON çıktı isteniyor: exit kodu
değişmez ama stdout tek satır JSON — `jq` veya benzeri araçlarla
alan çıkarma kolay.

## İhtiyaç (tek cümle)
`atlas doctor --json` bayrağı ile çıktı JSON formatında olsun
(tek satır); alan isimleri env değişkeni adlarına birebir eşleşsin;
API key hâlâ maskeli; uyarılar `warnings` array'inde.

## Ölçülebilir Başarı
- **M1 — Bayrak:** `atlas doctor --json` — insan formatı yerine JSON.
- **M2 — Şema:**
  ```json
  {
    "backend": {"ATLAS_LLM": "anthropic", "ANTHROPIC_API_KEY": "sk-***abc", ...},
    "retry_pricing": {"ATLAS_LLM_RETRIES": "0", ...},
    "storage": {"ATLAS_VAULT": "vault", ...},
    "warnings": ["ANTHROPIC_API_KEY yok", ...]
  }
  ```
- **M3 — API key maske:** aynı `_mask_secret` — tam key JSON'a asla
  düşmez.
- **M4 — Uyarı listesi:** insan formatındaki `[!]` prefix'li satırların
  metinleri (`[!] ` çıkarılmış); yoksa boş liste `[]`.
- **M5 — Exit 0** (021 kalıbı).
- **M6 — İnsan format değişmez:** `--json` yoksa 021 bit-uyumlu.
- **M7 — Test:** +4 test — JSON valid parse, backend key mask,
  warnings dolu, warnings boş.
- **M8 — DECISIONS:** [KARAR] neden env adları JSON'da; neden tek
  satır.

## Kapsam DIŞI
- YAML çıktı — `--json | yq -y` yeter.
- Sub-key nested detaylar (ör. tam anthropic model listesi).

## Kısıt
- `_cmd_doctor` yeniden yapılandırılabilir; şu anki string print
  ayrılmalı — veri toplama ve sunum ayrı.
- Türkçe uyarı metinleri korunur.

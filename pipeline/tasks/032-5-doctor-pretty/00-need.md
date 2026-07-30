# 032.5 — İhtiyaç: `atlas doctor --json --pretty`

## Bağlam
`atlas doctor --json` şu an tek satır. CI için ideal (jq/parse
kolay) ama insan gözle bakınca okunmaz. `--pretty` bayrağı
girintili basarsa **CI + insan hibrit** kullanım kolaylaşır:
```bash
$ atlas doctor --json --pretty | less
```

## İhtiyaç (tek cümle)
`atlas doctor --json --pretty` bayrağı verildiğinde JSON çıktısı
`indent=2` ile basılsın; yoksa mevcut tek satır davranışı korunsun.

## Ölçülebilir Başarı
- **M1 — Bayrak:** `atlas doctor --pretty` — `--json` ile birlikte
  anlamlı. Tek başına `--pretty` (JSON olmadan) sessizce yoksayılır
  (insan format zaten çok satırlı).
- **M2 — Girintili çıktı:** `json.dumps(report, indent=2, ensure_ascii=False)`.
  Satır sayısı >= 20 (mevcut şema derinliği yeterli).
- **M3 — Bit-uyumluluk:** `--pretty` yoksa tek satır çıktı; mevcut
  JSON tüketicileri değişmeden çalışır.
- **M4 — Strict davranışı:** `--pretty + --strict + drift` → exit 9
  hala tetikler (bayrak yalnız çıktı biçimlendirmesi).
- **M5 — Test:** +3 test — pretty ile çok satırlı, pretty yoksa
  tek satır, pretty + strict + drift.

## Kapsam DIŞI
- YAML çıktı — YAGNI.
- `--pretty --sort-keys` — YAGNI.
- Insan format için `--pretty` — insan format zaten okunur.

## Kısıt
- `_cmd_doctor` JSON çıktı davranışı BİREBİR (yalnız girintileme
  eklendi).
- Yeni env DEĞİL, yeni exit kodu YOK.

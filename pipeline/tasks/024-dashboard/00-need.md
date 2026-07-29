# 024 — İhtiyaç: `atlas dashboard` — audit + metrics özeti

## Bağlam
`.atlas/audit.jsonl` (SPEC 002+) tüm plan/observe/error/action kayıtlarını
tutuyor. SPEC 023 `metrics.jsonl` LLM usage kayıtlarını tutuyor. Ama
kullanıcı **son run'lar ne yaptı? kaç tamamlandı? toplam cost ne?**
sorularına cevap için `jq` script yazmak zorunda.

## İhtiyaç (tek cümle)
`atlas dashboard [--limit N]` alt-komutu `.atlas/audit.jsonl`'a
bakıp son N `atlas-run` "başlangıç → bitiş" oturumunu yakalasın;
tablo halinde: goal, exit sebebi (done/max_steps/error/denied),
süre, plan sayısı, metrics.jsonl'dan eşleşen zaman aralığındaki cost.

## Ölçülebilir Başarı
- **M1 — Run tespiti:** `actor == "atlas-run"` kayıtlarında `action`
  değerleri `plan` / `observe` / `done` / `denied` / `max_steps` /
  `llm_error` / `dry_run`. `dry_run` **veya** ilk `plan` bir run'ın
  başlangıcı; `done` / `denied` / `max_steps` / `llm_error` bitiş.
- **M2 — Grup mantığı:** kronolojik sırayla dolaş, run objelerine böl.
  Basit heuristic: `dry_run` **veya** `plan` başlangıç işareti;
  sonraki `done`/`denied`/`max_steps`/`llm_error` bitiş; bunlar
  arasındaki `plan` sayısını say.
- **M3 — Cost ilişkisi:** metrics.jsonl'daki `ts` alanı run başlangıç
  ile bitiş arasındaysa maliyet o run'a atanır. Fiyat env'i gerekir;
  yoksa cost `"?"`.
- **M4 — İnsan format:**
  ```
  === ATLAS dashboard — son 10 run ===
    #  ts                   exit         steps  cost
    1  2026-07-29 10:00:00  done         3      $0.012
    2  2026-07-29 10:15:00  max_steps    8      $0.045
    3  2026-07-29 10:30:00  llm_error    0      $0.000
    ...
  ```
- **M5 — JSON format:** `--json` liste.
- **M6 — Audit sağlık:** ilk satır olarak `denetim zinciri: GEÇERLİ /
  BOZULMUŞ` (`AuditLog.verify()`).
- **M7 — Boş dosya:** exit 0 + "0 run" mesajı.
- **M8 — Test:** +5 test — audit yok exit 0, single done run,
  max_steps run, llm_error run, JSON çıktı.
- **M9 — DECISIONS:** [KARAR] heuristic grup mantığı; audit sağlık
  ilk satır.

## Kapsam DIŞI
- Grafiksel HTML dashboard — YAGNI.
- Prometheus / Grafana entegrasyon.
- Run cost per goal type — YAGNI.

## Kısıt
- Read-only.
- Boş audit dosyası → boş dashboard (crash yok).
- Türkçe format.
